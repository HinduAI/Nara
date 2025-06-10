from dotenv import load_dotenv
import os
from openai import OpenAI
from typing import List, Optional, Dict
from datetime import datetime
from database import models
from utils.database import SessionLocal
from database.db_engine import get_or_create_conversation, store_message
from services.ref import HINDU_SYSTEM_PROMPT

# Initialize clients
load_dotenv()

conversation_history: Dict[str, List[Dict[str, str]]] = {}


def clean_response(text: str) -> str:
    """Clean and format the response text while preserving proper formatting."""

    # Don't strip all markdown - preserve headers and basic formatting
    # Only remove excessive formatting
    text = text.replace("***", "**")  # Convert triple asterisks to double

    # Clean up excessive newlines but preserve paragraph structure
    lines = text.splitlines()
    cleaned_lines = []
    prev_line_empty = False

    for line in lines:
        stripped_line = line.strip()

        # Skip excessive empty lines (allow max 1 empty line between content)
        if not stripped_line:
            if not prev_line_empty:
                cleaned_lines.append("")
            prev_line_empty = True
            continue

        # Preserve the line as-is for most cases
        cleaned_lines.append(stripped_line)
        prev_line_empty = False

    # Join with newlines
    text = "\n".join(cleaned_lines)

    # Ensure proper paragraph spacing - double newlines between paragraphs
    # Split on double newlines, clean each paragraph, then rejoin
    paragraphs = text.split("\n\n")
    cleaned_paragraphs = []

    for para in paragraphs:
        para = para.strip()
        if para:  # Only add non-empty paragraphs
            cleaned_paragraphs.append(para)

    # Join paragraphs with double newlines for proper spacing
    return "\n\n".join(cleaned_paragraphs)


def analyze_hindu_question(question: str) -> str:
    """Analyze the type of Hindu-related question being asked."""
    question = question.lower()

    if any(
        word in question
        for word in ["meaning", "translation", "sanskrit", "devanagari"]
    ):
        return "translation"
    elif any(
        word in question for word in ["philosophy", "concept", "theory", "principle"]
    ):
        return "philosophical"
    elif any(word in question for word in ["practice", "ritual", "worship", "puja"]):
        return "practical"
    elif any(word in question for word in ["story", "mythology", "purana", "itihasa"]):
        return "narrative"
    elif any(
        word in question for word in ["dharma", "duty", "responsibility", "ethics"]
    ):
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
        "approach": "Respond naturally and conversationally, weaving relevant Sanskrit texts, translations, context, and practical applications organically into a flowing narrative. Avoid numbered sections or rigid structures - let your wisdom unfold like a thoughtful conversation.",
    }

    return " ".join(components.values())


def ask_llm(user_question: str, user_id: str, user_email: str, conversation_id: int = None) -> Dict:
    """Main function to handle Hindu-related questions and analysis."""
    try:
        db = SessionLocal()
        OPENAI_CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        conversation = get_or_create_conversation(
            db, user_question, user_id, user_email, conversation_id
        )

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
            }
            for msg in messages
        ]

        # Generate the prompt
        prompt = generate_hindu_prompt(user_question)

        # Prepare messages for GPT API call
        gpt_messages = [
            {"role": "system", "content": HINDU_SYSTEM_PROMPT},
        ]

        # Add conversation history
        for msg in history:
            gpt_messages.append({"role": "user", "content": msg["user"]})
            gpt_messages.append({"role": "assistant", "content": msg["assistant"]})

        # Add the current question
        gpt_messages.append({"role": "user", "content": f"{prompt}\n\nQuestion: {user_question}"})

        completion = OPENAI_CLIENT.chat.completions.create(
            model="gpt-4o",
            messages=gpt_messages,
            temperature=0.7,
            max_tokens=5000,
        )

        final_response = clean_response(completion.choices[0].message.content)

        # Store the message
        store_message(
            db=db,
            conversation_id=conversation.id,
            user_message=user_question,
            assistant_message=final_response,
        )

        return {
            "response": final_response,
            "history": history,
            "conversation_id": conversation.id,
        }

    except Exception as e:
        print(f"Error in ask_llm: {str(e)}")
        return {"error": f"An error occurred: {str(e)}", "history": []}
    finally:
        db.close()