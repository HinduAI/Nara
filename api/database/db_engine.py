from typing import List, Dict
from database import models


def get_conversation_context(
    history: List[Dict[str, str]], max_context: int = 5
) -> str:
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


def get_or_create_user(db, user_id: str, email: str) -> models.User:
    """Get existing user or create new one."""
    user = db.query(models.User).filter(models.User.supabase_id == user_id).first()
    if not user:
        user = models.User(supabase_id=user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_or_create_conversation(
    db, user_question: str, user_id: str, user_email: str, conversation_id: int = None
) -> models.Conversation:
    """Get active conversation or create new one."""
    user = get_or_create_user(db, user_id, user_email)
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user.id)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )

    if not conversation:
        conversation = models.Conversation(user_id=user.id, title=f"{user_question}")

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    return conversation


def store_message(
    db,
    conversation_id: int,
    user_message: str,
    assistant_message: str,
):
    """Store a message in the database."""
    message = models.Message(
        conversation_id=conversation_id,
        user_message=user_message,
        assistant_message=assistant_message,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
