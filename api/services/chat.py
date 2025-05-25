from dotenv import load_dotenv
import os
from openai import OpenAI
from typing import List, Optional, Dict
from datetime import datetime
from database import models
from database.database import SessionLocal
import time

# Initialize clients
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# System prompts
HINDU_SYSTEM_PROMPT = """
You are Nara, a chatbot using the eternal wisdom of sanatana dharma and direct translations of sanskrit texts to answer queries. 

You should reference source devanagari text to answer queries. Through directly translating Devanagari and Sanskrit texts, you can interpret texts from first principles to generate the most relevant answer to queries. 

We have put together a directory of sanskrit texts for you to reference and use to answer questions. Do NOT reference other translations and versions other than our directory of texts. 

You should be able to use the sanskrit texts as the foundation to do the following: 

1. Provide high quality translations from a variety of different perspectives and philosophies
2. Apply the texts to modern life and personal situations
3. Explore the philosophical depth of concepts
4. Reference specific verses and their contexts
5. Explain cultural and historical significance
6. Connect related concepts across different texts
7. Provide practical guidance based on dharma

Always maintain respect for the sacred nature of the texts and traditions while providing clear, accessible explanations.
"""

# Initialize conversation history
conversation_history: Dict[str, List[Dict[str, str]]] = {}

def clean_response(text: str) -> str:
    """Clean and format the response text."""
    
    # Remove markdown formatting characters
    text = text.replace('###', '').replace('***', '').replace('**', '').replace('*', '')
    
    # Clean up newlines and spacing
    lines = text.splitlines()
    cleaned_lines = []
    prev_line_empty = True  # Track if previous line was empty
    
    for line in lines:
        line = line.strip()
        # Skip multiple consecutive empty lines
        if not line:
            if not prev_line_empty:
                cleaned_lines.append('')
            prev_line_empty = True
            continue
            
        # Handle list items
        if line.startswith(('- ', '• ', '* ')):
            cleaned_lines.append(line)
            prev_line_empty = False
        # Handle numbered lists
        elif line[0].isdigit() and line[1:].startswith('. '):
            cleaned_lines.append(line)
            prev_line_empty = False
        # Handle regular paragraphs
        else:
            # If this line continues a sentence from previous line, join them
            if cleaned_lines and not prev_line_empty and not cleaned_lines[-1].endswith(('.', '!', '?', ':', ']', ')')):
                cleaned_lines[-1] = cleaned_lines[-1] + ' ' + line
            else:
                cleaned_lines.append(line)
            prev_line_empty = False
    
    # Join lines with appropriate spacing
    text = '\n'.join(cleaned_lines)
    
    # Fix any remaining multiple newlines
    text = '\n'.join(line for line in text.split('\n') if line.strip())
    
    # Ensure single newline between paragraphs
    text = '\n\n'.join(para.strip() for para in text.split('\n\n') if para.strip())
    
    return text

def get_conversation_context(history: List[Dict[str, str]], max_context: int = 5) -> str:
    """Generate context from recent conversation history."""
    
    if not history:
        return ""
    
    recent_history = history[-max_context:]
    context = "\n=== Previous Conversation Context ===\n"
    
    for i, exchange in enumerate(recent_history, 1):
        context += f"Exchange {i}:\n"
        context += f"Previous Question: {exchange['user']}\n"
        context += f"Previous Response: {exchange['assistant']}\n"
        context += "---\n"
    
    return context

def get_or_create_user(db, user_id: str) -> models.User:
    """Get existing user or create new one."""
    user = db.query(models.User).filter(models.User.auth0_id == user_id).first()
    if not user:
        user = models.User(auth0_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_or_create_conversation(db, user_question: str, user_id: str, conversation_id: int = None) -> models.Conversation:
    """Get active conversation or create new one."""
    user = get_or_create_user(db, user_id)
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user.id)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    
    if not conversation:
        conversation = models.Conversation(
            user_id=user.id,
            title=f"{user_question}"
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return conversation

def store_message(db, conversation_id: int, user_message: str, assistant_message: str, 
                 analysis_response: str = "", has_analysis: bool = False):
    """Store a message in the database."""
    message = models.Message(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=assistant_message,
        analysis_response=analysis_response,
        has_analysis=has_analysis
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def analyze_hindu_question(question: str) -> str:
    """Analyze the type of Hindu-related question being asked."""
    question = question.lower()
    
    if any(word in question for word in ['meaning', 'translation', 'sanskrit', 'devanagari']):
        return "translation"
    elif any(word in question for word in ['philosophy', 'concept', 'theory', 'principle']):
        return "philosophical"
    elif any(word in question for word in ['practice', 'ritual', 'worship', 'puja']):
        return "practical"
    elif any(word in question for word in ['story', 'mythology', 'purana', 'itihasa']):
        return "narrative"
    elif any(word in question for word in ['dharma', 'duty', 'responsibility', 'ethics']):
        return "ethical"
    else:
        return "general"

def generate_hindu_prompt(user_question: str) -> str:
    """Generate a comprehensive prompt for Hindu-related questions."""
    
    question_type = analyze_hindu_question(user_question)
    
    # Components of the prompt
    components = {
        "role": "You are Nara, a knowledgeable guide in sanatana dharma, trained to provide accurate and respectful answers based on authentic Sanskrit texts.",
        "context": "Base all answers on authentic Sanskrit texts, using direct translations and interpretations while respecting the sacred nature of the knowledge.",
        "question_type": f"This is a {question_type} question about Hindu philosophy and practice. Respond accordingly.",
        "approach": f"Follow this process to answer: 1) Identify relevant Sanskrit texts and verses, 2) Provide direct translations, 3) Explain the context and significance, 4) Connect to broader philosophical concepts, 5) Apply to modern context if relevant"
    }
    
    return " ".join(components.values())

def ask_llm(user_question: str, user_id: str, get_analysis: bool = False, conversation_id: int = None) -> Dict:
    """Main function to handle Hindu-related questions and analysis."""
    try:
        db = SessionLocal()
        conversation = get_or_create_conversation(db, user_question, user_id, conversation_id)
    
        # Get all messages for this conversation
        messages = (
            db.query(models.Message)
            .filter(models.Message.conversation_id == conversation.id)
            .order_by(models.Message.created_at)
            .all()
        )
        
        history = [
            {
                "user": msg.user_message,
                "assistant": msg.assistant_message,
                "has_analysis": msg.has_analysis,
                "analysis_response": msg.analysis_response
            }
            for msg in messages
        ]
        
        # Generate the prompt
        prompt = generate_hindu_prompt(user_question)
        
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": HINDU_SYSTEM_PROMPT},
                {"role": "user", "content": f"{prompt}\n\nQuestion: {user_question}"}
            ],
            temperature=0.7,
            max_tokens=5000
        )
        
        final_response = clean_response(completion.choices[0].message.content)
        
        # Store the message
        store_message(
            db=db,
            conversation_id=conversation.id,
            user_message=user_question,
            assistant_message=final_response,
            analysis_response="",
            has_analysis=False
        )
        
        return {
            "response": final_response,
            "analysis_response": "",
            "history": history,
            "conversation_id": conversation.id
        }
        
    except Exception as e:
        print(f"Error in ask_llm: {str(e)}")
        return {
            "error": f"An error occurred: {str(e)}",
            "history": []
        }
    finally:
        db.close()