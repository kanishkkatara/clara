from typing import List
from uuid import UUID
from openai import OpenAI
import os
import json
from sqlalchemy.orm import Session
from app.models.memory import UserMemory
from app.models.profile import UserProfile
from app.models.user import User

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Generate embeddings
def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# --- Fetch onboarding memory chronologically
def fetch_onboarding_memories(db: Session, user_id: UUID) -> List[UserMemory]:
    return db.query(UserMemory)\
        .filter(UserMemory.user_id == user_id, UserMemory.type == "onboarding")\
        .order_by(UserMemory.id.asc())\
        .all()

# --- Build system + chat messages
def build_onboarding_prompt(memories: List[UserMemory], user_input: str):
    memory_blocks = "\n".join([f"{m.source.upper()}: {m.message}" for m in memories])

    system = (
        "You are Clara, a friendly and conversational onboarding assistant for a GMAT prep app.\n\n"
        "You're talking to a new user and your job is to get to know them.\n"
        "During the conversation, collect three fields naturally:\n"
        "1. exam (e.g., GMAT, GRE)\n"
        "2. country (where they live)\n"
        "3. goals (target score or focus areas)\n\n"
        "Do NOT ask these like a form. Instead:\n"
        "- Ask follow-up questions\n"
        "- Reference earlier replies\n"
        "- Use light humor or empathy\n"
        "- Do not repeat what's already answered\n\n"
        "Once you have all 3, end with a friendly summary and include:\n"
        "final_profile: {\"exam\": \"GMAT\", \"country\": \"India\", \"goals\": \"Target 720, focus on quant\"}\n\n"
        "If only 1 or 2 are known, continue asking and optionally include:\n"
        "partial_profile: {\"exam\": \"GMAT\"}\n\n"
        f"Here’s the chat so far:\n{memory_blocks}"
    )

    messages = [{"role": "system", "content": system}]
    for m in memories:
        messages.append({"role": m.source, "content": m.message})
    messages.append({"role": "user", "content": user_input})
    return messages

# --- Main handler
async def handle_onboarding(db: Session, user_id: UUID, user_input: str):
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    # ✅ Skip if onboarding already done
    if profile and getattr(profile, "onboarding_complete", False):
        return {
            "reply": (
                f"You're all set, {user.name.split()[0] if user else 'friend'}! 🎉\n\n"
                f"✅ Exam: {profile.exam or '-'}\n"
                f"🌍 Country: {profile.country or '-'}\n"
                f"🎯 Goals: {profile.goals or '-'}\n\n"
                "Let’s get started with your personalized prep journey!"
            ),
            "snippets_used": [],
            "onboarding_complete": True
        }

    # 🟡 Initial welcome message
    if user_input.lower() in ["__init__", "hi", "hello"]:
        first_name = user.name.split()[0] if user and user.name else "there"
        welcome = (
            f"Hey {first_name}! 👋 I’m Clara, your GMAT prep buddy. "
            "Excited to get to know you. To kick things off, tell me a little about yourself — "
            "what you do, what made you decide to go for the GMAT, or just anything random 😄"
        )
        emb = get_embedding(welcome)
        db.add(UserMemory(
            user_id=user_id,
            message=welcome,
            embedding=emb,
            type="onboarding",
            source="assistant"
        ))
        db.commit()
        return {
            "reply": welcome,
            "snippets_used": [],
            "onboarding_complete": False
        }

    # 🔹 Store user message
    user_emb = get_embedding(user_input)
    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=user_emb,
        type="onboarding",
        source="user"
    ))
    db.commit()

    # 🔹 Build memory + prompt
    memories = fetch_onboarding_memories(db, user_id)
    messages = build_onboarding_prompt(memories, user_input)

    # 🔹 Call GPT
    chat = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    reply_msg = chat.choices[0].message
    reply_text = reply_msg.content or ""

    # 🔹 Always save assistant reply
    reply_emb = get_embedding(reply_text)
    db.add(UserMemory(
        user_id=user_id,
        message=reply_text,
        embedding=reply_emb,
        type="onboarding",
        source="assistant"
    ))
    db.commit()

    # 🔹 Parse final or partial profile
    parsed_json = None
    key_found = None
    for key in ["final_profile", "partial_profile"]:
        if key in reply_text.lower():
            try:
                json_start = reply_text.lower().index(f"{key}:") + len(f"{key}:")
                json_part = reply_text[json_start:].strip()
                parsed_json = json.loads(json_part)
                key_found = key
                break
            except Exception as e:
                print(f"⚠️ Failed to parse {key}: {e}")

    onboarding_complete = False

    # 🔹 Save to DB if final_profile
    if parsed_json and key_found == "final_profile":
        onboarding_complete = True
        if profile:
            for k, v in parsed_json.items():
                setattr(profile, k, v)
            profile.onboarding_complete = True
        else:
            db.add(UserProfile(user_id=user_id, onboarding_complete=True, **parsed_json))
        db.commit()

    return {
        "reply": reply_text,
        "snippets_used": [m.message for m in memories],
        "onboarding_complete": onboarding_complete
    }
