import sys
import os
# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Union
from services.chat import *
from fastapi.middleware.cors import CORSMiddleware
from database import models, database
from database.database import engine, get_db
from sqlalchemy.orm import Session

app = FastAPI()

origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    user_id: str
    conversation_id: Optional[int] = None
    get_analysis: Optional[bool] = False

class QuestionResponse(BaseModel):
    response: str
    exa_response: str = ""
    analysis_response: str = ""
    history: List[Dict]

@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        result = ask_llm(
            request.question,
            request.user_id,
            request.get_analysis,
            request.conversation_id
        )
        
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])
            
        return QuestionResponse(
            response=result['response'] or "",
            exa_response=result.get('exa_response', ""),
            analysis_response=result.get('analysis_response', ""),
            history=result['history']
        )
    except Exception as e:
        print('Exception in ask_question: ', e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/createnewconversation")
async def create_new_conversation(request: dict, db: Session = Depends(get_db)):
    try:
        user_id = request.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")

        user = db.query(models.User).filter(models.User.auth0_id == user_id).first()
        if not user:
            user = models.User(auth0_id=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)

        conversation = models.Conversation(
            user_id=user.id,
            title=request.get("question")
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return {
            "id": conversation.id,
            "title": conversation.title
        }
    except Exception as e:
        print(f"Error creating new conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{user_id}")
async def get_all_conversations(user_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.auth0_id == user_id).first()
    if not user:
        return []
    
    conversations = db.query(models.Conversation)\
        .filter(models.Conversation.user_id == user.id)\
        .order_by(models.Conversation.updated_at.desc())\
        .all()
    
    return [{"id": c.id, "title": c.title} for c in conversations]

@app.get("/api/conversations/{conversation_id}/messages")
async def get_all_messages(conversation_id: int, db: Session = Depends(get_db)):
    messages = db.query(models.Message)\
        .filter(models.Message.conversation_id == conversation_id)\
        .order_by(models.Message.created_at)\
        .all()
    
    return [
        {
            "id": msg.id,
            "user": msg.user_message,
            "assistant": msg.assistant_message,
            "has_analysis": msg.has_analysis,
            "exa_response": msg.exa_response,
            "analysis_response": msg.analysis_response
        }
        for msg in messages
    ]

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    db.delete(conversation)
    db.commit()
    return {"status": "success"}

@app.put("/api/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: int, 
    title_update: dict, 
    db: Session = Depends(get_db)
):
    try:
        conversation = db.query(models.Conversation)\
            .filter(models.Conversation.id == conversation_id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation.title = title_update["title"]
        db.commit()
        
        return {"status": "success", "id": conversation_id, "title": title_update["title"]}
    except Exception as e:
        print(f"Error updating conversation title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/messages/{message_id}/feedback")
async def update_message_feedback(
    message_id: int, 
    feedback: dict,
    db: Session = Depends(get_db)
):
    try:
        message = db.query(models.Message).filter(models.Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        message.response_liked = feedback["response_liked"]
        db.commit()
        
        return {"status": "success", "message": "Feedback updated successfully"}
    except Exception as e:
        print(f"Error updating message feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))