# src/app/api/chat.py

from typing import Any, Dict, Optional
from fastapi import APIRouter, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db
from app.services import onboarding_bot, tutoring_bot

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    chat_type: str
    context: Optional[Dict[str, Any]] = None

@router.post("/message")
async def chat_entry(
    body: ChatRequest,
    x_user_id: int = Header(...),
    db: Session = Depends(get_db)
):
    if body.chat_type == "onboarding":
        return await onboarding_bot.handle_onboarding(db, x_user_id, body.message)

    elif body.chat_type == "tutoring":
        return await tutoring_bot.handle_tutoring(
            db, x_user_id, body.message, body.context
        )

    return {"error": "Invalid chat_type"}
