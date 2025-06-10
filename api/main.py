import sys
import os
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Union
from services.chat import *
from fastapi.middleware.cors import CORSMiddleware
from database import models
from utils.database import engine, get_db
from sqlalchemy.orm import Session
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configure CORS - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"]  # Expose all headers
)

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        # Remove 'Bearer ' from the token
        token = authorization.replace('Bearer ', '')
        # Verify the JWT token with Supabase
        user = supabase.auth.get_user(token)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    get_analysis: Optional[bool] = False


class QuestionResponse(BaseModel):
    response: str
    exa_response: str = ""
    analysis_response: str = ""
    history: List[Dict]


@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, user = Depends(get_current_user)):
    try:
        result = ask_llm(
            request.question,
            user.user.id,
            user.user.email,
            request.conversation_id,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return QuestionResponse(
            response=result["response"] or "",
            exa_response=result.get("exa_response", ""),
            analysis_response=result.get("analysis_response", ""),
            history=result["history"],
        )
    except Exception as e:
        print("Exception in ask_question: ", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/createnewconversation")
async def create_new_conversation(request: dict, user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        if not user:
            raise HTTPException(status_code=400, detail="User not found")

        user_db = db.query(models.User).filter(models.User.supabase_id == user.user.id).first()
        if not user_db:
            user_db = models.User(supabase_id=user.user.id, email=user.user.email)
            db.add(user_db)
            db.commit()
            db.refresh(user_db)

        conversation = models.Conversation(
            user_id=user_db.id, title=request.get("question")
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return {"id": conversation.id, "title": conversation.title}
    except Exception as e:
        print(f"Error creating new conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations")
async def get_all_conversations(user = Depends(get_current_user), db: Session = Depends(get_db)):
    user_db = db.query(models.User).filter(models.User.supabase_id == user.user.id).first()
    if not user_db:
        return []

    conversations = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user_db.id)
        .order_by(models.Conversation.updated_at.desc())
        .all()
    )

    return [{"id": c.id, "title": c.title} for c in conversations]


@app.get("/api/conversations/{conversation_id}/messages")
async def get_all_messages(conversation_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation_id)
        .order_by(models.Message.created_at)
        .all()
    )

    return [
        {
            "id": msg.id,
            "user": msg.user_message,
            "assistant": msg.assistant_message,
        }
        for msg in messages
    ]


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conversation_id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"status": "success"}


@app.put("/api/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: int, title_update: dict, db: Session = Depends(get_db)
):
    try:
        conversation = (
            db.query(models.Conversation)
            .filter(models.Conversation.id == conversation_id)
            .first()
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.title = title_update["title"]
        db.commit()

        return {
            "status": "success",
            "id": conversation_id,
            "title": title_update["title"],
        }
    except Exception as e:
        print(f"Error updating conversation title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/messages/{message_id}/feedback")
async def update_message_feedback(
    message_id: int, feedback: dict, db: Session = Depends(get_db)
):
    try:
        message = (
            db.query(models.Message).filter(models.Message.id == message_id).first()
        )
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        message.response_liked = feedback["response_liked"]
        db.commit()

        return {"status": "success", "message": "Feedback updated successfully"}
    except Exception as e:
        print(f"Error updating message feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
