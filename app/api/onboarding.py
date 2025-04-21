from fastapi import APIRouter, Request, Header
from pydantic import BaseModel
from typing import Optional, Dict, List
from app.services.onboarding_chatbot import OnboardingChatbot
from dotenv import load_dotenv
import os
import openai

router = APIRouter()
load_dotenv()

onboarding_bot = OnboardingChatbot()  # No need to pass openai client anymore

# In-memory store for chat history. Replace with Redis or DB for production.
session_histories: Dict[str, List[str]] = {}

class ChatRequest(BaseModel):
    user_input: str

@router.post("/chat")
def chatbot_interaction(request: Request, chat: ChatRequest, x_user_id: Optional[str] = Header(None)):
    print(f"--> Received request: {chat.user_input}")
    if not x_user_id:
        return {"error": "Missing X-User-ID header"}

    # Track user session
    print(f"--> Current session history: {session_histories}")
    history = session_histories.setdefault(x_user_id, [])

    # Append user message
    history.append(f"User: {chat.user_input}")

    # Get bot response
    print(f"--> Asking chatbot to generate response.")
    bot_reply = onboarding_bot.chat(history)

    # Append bot reply
    history.append(f"Bot: {bot_reply}")

    return {"reply": bot_reply}
