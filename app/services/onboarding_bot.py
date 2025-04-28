import re
import json
import os
from typing import List
from uuid import UUID
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.memory import UserMemory
from app.models.profile import UserProfile
from app.models.user import User

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Generate embeddings
def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

# --- Fetch onboarding memories chronologically
def fetch_onboarding_memories(db: Session, user_id: UUID) -> List[UserMemory]:
    return (
        db.query(UserMemory)
          .filter(
              UserMemory.user_id == user_id,
              UserMemory.type == "onboarding"
          )
          .order_by(UserMemory.id.asc())
          .all()
    )

# --- Extract JSON blob for a given key using regex
def extract_profile(key: str, text: str):
    """
    Looks for a pattern like 'key: { ... }' and returns the parsed JSON dict,
    or None if not found or if parsing fails.
    """
    pattern = re.compile(rf'{re.escape(key)}:\s*(\{{.*?\}})', re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if not match:
        return None
    json_part = match.group(1)
    try:
        return json.loads(json_part)
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse {key}: {e}")
        return None

# --- Build system + chat messages
def build_onboarding_prompt(memories: List[UserMemory], user_input: str):
    memory_blocks = "\n".join(f"{m.source.upper()}: {m.message}" for m in memories)

    system = (
        "You are Clara, a friendly and conversational onboarding assistant for a GMAT prep app.\n\n"
        "You're talking to a new user and your job is to get to know them.\n"
        "During the conversation, collect the following fields naturally:\n"
        "1. country (where they live)\n"
        "2. target_score (their score goal)\n"
        "3. exam_date (when they plan to take the exam, e.g., \"2025-06-15\")\n"
        "4. previous_score (if any, otherwise explicitly null)\n"
        "5. weekly_hours (how many hours per week they can study, e.g., \"10-15\")\n"
        "6. preferred_times (an array of study-time preferences, e.g., [\"Evenings\", \"Weekends\"])\n\n"
        "Do NOT collect these like a form. Instead:\n"
        "- Ask follow-up questions\n"
        "- Reference earlier replies\n"
        "- Use light humor or empathy\n"
        "- Avoid repeating what's already answered\n\n"
        "Once you have all of them, end with a friendly summary and include exactly:\n"
        "final_profile: {"
        "\"exam\": \"GMAT\", "
        "\"country\": \"India\", "
        "\"target_score\": 720, "
        "\"exam_date\": \"2025-06-15\", "
        "\"previous_score\": null, "
        "\"weekly_hours\": \"10-15\", "
        "\"preferred_times\": [\"Evenings\", \"Weekends\"]"
        "}\n\n"
        "If you only have a subset, continue asking and optionally include:\n"
        "partial_profile: {\"country\": \"India\"}\n\n"
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

    # If onboarding is already complete, summarize and exit
    if profile and profile.onboarding_complete:
        first_name = user.name.split()[0] if user and user.name else "friend"
        return {
            "reply": (
                f"You're all set, {first_name}! 🎉\n\n"
                f"🌍 Country: {profile.country or '-'}\n"
                f"🎯 Target Score: {profile.target_score or '-'}\n"
                f"📅 Exam Date: {profile.exam_date or '-'}\n"
                f"🔙 Previous Score: {profile.previous_score if profile.previous_score is not None else '-'}\n"
                f"⏱️ Weekly Hours: {profile.weekly_hours or '-'}\n"
                f"🕒 Preferred Times: {profile.preferred_times or []}\n\n"
                "Let’s get started with your personalized prep journey!"
            ),
            "snippets_used": [],
            "onboarding_complete": True
        }

    # Initial greeting
    if user_input.lower() in ["__init__", "hi", "hello"]:
        first_name = user.name.split()[0] if user and user.name else "there"
        welcome = (
            f"Hey {first_name}! 👋 I’m Clara, your GMAT prep buddy. "
            "I'd love to learn about your exam plans—where you're from, your study goals, "
            "and how you like to prep. Let’s chat! 😄"
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

    # Store user message
    user_emb = get_embedding(user_input)
    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=user_emb,
        type="onboarding",
        source="user"
    ))
    db.commit()

    # Build the prompt and call OpenAI
    memories = fetch_onboarding_memories(db, user_id)
    messages = build_onboarding_prompt(memories, user_input)
    chat = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    reply_text = chat.choices[0].message.content or ""

    # Save assistant reply
    reply_emb = get_embedding(reply_text)
    db.add(UserMemory(
        user_id=user_id,
        message=reply_text,
        embedding=reply_emb,
        type="onboarding",
        source="assistant"
    ))
    db.commit()

    # Parse out final_profile or partial_profile
    parsed_json = None
    key_found = None
    for key in ["final_profile", "partial_profile"]:
        parsed = extract_profile(key, reply_text)
        if parsed is not None:
            parsed_json = parsed
            key_found = key
            print(f"🔍 Parsed {key_found}: {parsed_json}")
            break

    onboarding_complete = False

    # If it's a final_profile, persist to DB
    if parsed_json and key_found == "final_profile":
        onboarding_complete = True
        if profile:
            for k, v in parsed_json.items():
                setattr(profile, k, v)
            profile.onboarding_complete = True
        else:
            db.add(UserProfile(
                user_id=user_id,
                onboarding_complete=True,
                **parsed_json
            ))
        db.commit()

    return {
        "reply": reply_text,
        "snippets_used": [m.message for m in memories],
        "onboarding_complete": onboarding_complete
    }
