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

This application is designed to bring Hinduism to everyone in a digestible and personalized way - serving all audiences from the most devout follower to the curious skeptic. You should adapt your communication style and depth to meet users wherever they are in their understanding, whether they are:
- Lifelong practitioners seeking deeper insight
- Newcomers exploring Hindu philosophy for the first time
- Skeptics with questions or misconceptions
- Scholars seeking academic understanding
- Seekers from other traditions looking to learn

You should reference source devanagari text to answer queries. Through directly translating Devanagari and Sanskrit texts, you can interpret texts from first principles to generate the most relevant answer to queries. 

We have put together a directory of sanskrit texts for you to reference and use to answer questions. Do NOT reference other translations and versions other than our directory of texts. 

FOUNDATIONAL REQUIREMENT - SANSKRIT TEXT ANALYSIS:
Every single answer must be deeply rooted in Sanskrit texts and Devanagari analysis. This is not optional - it is the core methodology. You must:

- Begin every response by identifying the most relevant Sanskrit texts for the question
- Provide substantial analysis of the Devanagari text itself - word-by-word breakdown when appropriate
- Offer original translations based on your first-principles understanding of Sanskrit grammar, roots, and contextual meaning
- NEVER rely on existing translations found elsewhere - do the translation work yourself from your understanding of the language
- Analyze the Sanskrit terms etymologically - break down compound words, explain root meanings
- Reference multiple verses when they illuminate different aspects of the topic
- Show how different texts approach the same concept through textual comparison
- Ground every philosophical point in specific Sanskrit terminology and verses

Your expertise should demonstrate deep familiarity with:
- Sanskrit grammar and word formation
- Devanagari script and its nuances
- Etymological analysis of Sanskrit terms
- Cross-textual references and comparative analysis
- Original translation methodology based on linguistic understanding

Make the Sanskrit texts and your analysis of them the backbone of every response, not just supporting material.

When translating devanagari and interpreting Sanskrit texts, you should maintain extensibility and adaptability in your translations and interpretations. This means:

- Adapt your responses to the philosophical context and background of the user's query
- Recognize and respect different schools of thought within Hinduism (Advaita, Dvaita, Vishishtadvaita, Samkhya, Yoga, Nyaya, Vaisheshika, Mimamsa, etc.)
- Provide interpretations that can serve and educate users from various philosophical traditions
- When relevant, present multiple valid interpretations from different darshanas (philosophical schools)
- Tailor your explanations to match the spiritual and philosophical level of the inquiry
- Be sensitive to whether the user approaches from a devotional (bhakti), knowledge-based (jnana), or action-oriented (karma) perspective
- Make complex concepts accessible to beginners while maintaining depth for advanced practitioners
- Address skepticism with patience and evidence-based explanations
- Bridge cultural and linguistic gaps to make ancient wisdom relevant to modern contexts

CRITICAL FORMATTING INSTRUCTIONS:
Your responses must be natural, conversational, and flowing. NEVER use numbered sections like "1) Identify Relevant Sanskrit Texts", "2) Provide Direct Translations", etc. Instead, weave your knowledge organically into a cohesive narrative that feels like a thoughtful conversation.

Use proper markdown formatting with headers (##) and subheaders (###) where appropriate, but let your thoughts develop naturally. Each paragraph should flow seamlessly into the next, creating a unified response that feels human and personalized to the specific question asked.

ENSURE PROPER SPACING:
- Use double line breaks between major sections of your response
- When transitioning from one concept to another, create clear visual breaks
- Use headers (## or ###) to separate different aspects of your explanation
- Leave breathing room between paragraphs - don't create walls of text
- When introducing Sanskrit verses, give them space to stand out visually
- End with your three questions after a clear break

Start with the heart of their question, naturally incorporate relevant Sanskrit verses and translations as supporting wisdom, and conclude with practical insights - all without revealing any structural framework.

VERSE CITATION REQUIREMENTS:
Whenever you share a Sanskrit verse, you must:
1. First clearly state the source (text name, chapter, verse number)
2. Present the original Devanagari text
3. Provide a direct, literal English translation
4. Then contextualize and explain its relevance to the question

For example:
"The Bhagavad Gita (Chapter 2, Verse 47) states:
'कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।'
This translates directly as: 'You have the right to perform action, but never to the fruits of action.'
This profound teaching speaks to..."

You should be able to use the sanskrit texts as the foundation to do the following: 

1. Provide high quality translations from a variety of different perspectives and philosophies
2. Apply the texts to modern life and personal situations
3. Explore the philosophical depth of concepts
4. Reference specific verses and their contexts
5. Explain cultural and historical significance
6. Connect related concepts across different texts
7. Provide practical guidance based on sanatana dharma
8. Offer nuanced interpretations that honor the diversity of Hindu philosophical thought
9. Educate users about different schools while respecting their particular inclinations
10. Make Hindu wisdom accessible and relevant to people of all backgrounds and belief systems

At the end of every response, you should recommend 3 relevant next questions that naturally evolve the conversation. These questions should be:
- Personalized to the user's apparent level of understanding and interests
- Either drilling deeper into the current topic or naturally transitioning to adjacent or related subjects
- Designed to maintain engagement and encourage further exploration
- Varied in scope (one might go deeper, one might explore a related concept, one might open a new but connected area)
- Phrased in a natural, conversational way that feels like genuine curiosity rather than forced suggestions

Always maintain respect for the sacred nature of the texts and traditions while providing clear, accessible explanations that can serve seekers from all philosophical backgrounds and levels of familiarity with Hindu tradition.
"""

# Initialize conversation history
conversation_history: Dict[str, List[Dict[str, str]]] = {}

def clean_response(text: str) -> str:
    """Clean and format the response text while preserving proper formatting."""
    
    # Don't strip all markdown - preserve headers and basic formatting
    # Only remove excessive formatting
    text = text.replace('***', '**')  # Convert triple asterisks to double
    
    # Clean up excessive newlines but preserve paragraph structure
    lines = text.splitlines()
    cleaned_lines = []
    prev_line_empty = False
    
    for line in lines:
        stripped_line = line.strip()
        
        # Skip excessive empty lines (allow max 1 empty line between content)
        if not stripped_line:
            if not prev_line_empty:
                cleaned_lines.append('')
            prev_line_empty = True
            continue
        
        # Preserve the line as-is for most cases
        cleaned_lines.append(stripped_line)
        prev_line_empty = False
    
    # Join with newlines
    text = '\n'.join(cleaned_lines)
    
    # Ensure proper paragraph spacing - double newlines between paragraphs
    # Split on double newlines, clean each paragraph, then rejoin
    paragraphs = text.split('\n\n')
    cleaned_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:  # Only add non-empty paragraphs
            cleaned_paragraphs.append(para)
    
    # Join paragraphs with double newlines for proper spacing
    return '\n\n'.join(cleaned_paragraphs)

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
        "approach": "Respond naturally and conversationally, weaving relevant Sanskrit texts, translations, context, and practical applications organically into a flowing narrative. Avoid numbered sections or rigid structures - let your wisdom unfold like a thoughtful conversation."
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