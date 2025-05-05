import datetime
import re
import json
import os
from typing import List, Optional, Dict, Any
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


# --- Extract JSON blob for a given key using regex, trimming trailing commas
def extract_profile(key: str, text: str) -> Optional[Dict[str, Any]]:
    """
    Looks for a pattern like 'key: { ... }' and returns the parsed JSON dict,
    or None if not found or if parsing fails.
    """
    pattern = re.compile(
        rf'{re.escape(key)}\s*:\s*(\{{(?:[^{{}}]|\{{|\}})*\}})',
        re.IGNORECASE | re.DOTALL
    )
    match = pattern.search(text)
    if not match:
        return None

    json_part = match.group(1)
    cleaned = re.sub(r',\s*}', '}', json_part)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse {key}: {e}\nCleaned JSON was: {cleaned}")
        return None


# --- Build system + chat messages
def build_onboarding_prompt(memories: List[UserMemory], user_input: str) -> List[Dict[str, str]]:
    memory_blocks = "\n".join(f"{m.source.upper()}: {m.message}" for m in memories)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    system = (
        "You are Clara, a friendly but very concise onboarding assistant for a GMAT prep app.\n\n"
        "Your job:\n"
        "- Collect these 4 fields naturally: country, target_score, exam_date, previous_score.\n"
        "- NEVER generate long explanations or general facts. Replies should be short, crisp, and conversational.\n"
        "- If the user gives a vague or incomplete answer, assume and IMMEDIATELY register a reasonable value in partial_profile. Proceed without waiting for confirmation.\n"
        "- If the user later disagrees or provides a different value, update the partial_profile accordingly.\n"
        "- If the user does not answer the current question directly or changes the topic, assume a reasonable value and proceed without re-asking.\n"
        "- When assuming a date, always pick a FUTURE date (today or later).\n"
        f"- Assume today's date is {today_str}.\n"
        "- Once a field is captured or assumed, never ask about it again.\n"
        "- Every reply should either ask a follow-up question or confirm progress, so the user always has something to respond to. Continue this until all 4 fields are captured.\n"
        "- Use light, friendly confirmations like 'Got it!' or 'Sounds good!' instead of repeating the user's response fully.\n"
        "- Use the user's name once mid-conversation to make it feel personal.\n"
        "- ALWAYS include the updated partial_profile after each new field is captured or assumed.\n"
        "- Finish collecting one field fully before moving to the next.\n"
        "- Use a warm and friendly tone, avoid filler text or generic commentary.\n\n"
        "Once all 4 fields are known or assumed, even if any field is null, summarize them exactly like this:\n"
        "final_profile: {"
        "\"exam\": \"GMAT\", "
        "\"country\": \"India\", "
        "\"target_score\": 720, "
        "\"exam_date\": \"2025-06-15\", "
        "\"previous_score\": null"
        "}\n\n"
        "If only some fields are known, include:\n"
        "partial_profile: {\"country\": \"India\"}\n\n"
        f"Here’s the chat so far:\n{memory_blocks}"
    )


    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    for m in memories:
        messages.append({"role": m.source, "content": m.message})
    messages.append({"role": "user", "content": user_input})
    return messages


# --- Main handler
async def handle_onboarding(db: Session, user_id: UUID, user_input: str) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if profile and profile.onboarding_complete:
        first_name = user.name.split()[0] if user and user.name else "friend"
        return {
            "reply": (
                f"You're all set, {first_name}! 🎉\n\n"
                f"🌍 Country: {profile.country or '-'}\n"
                f"🎯 Target Score: {profile.target_score or '-'}\n"
                f"📅 Exam Date: {profile.exam_date or '-'}\n"
                f"🔙 Previous Score: {profile.previous_score if profile.previous_score is not None else '-'}\n"
                "Let’s get started with your personalized prep journey!"
            ),
            "snippets_used": [],
            "onboarding_complete": True
        }

    # Initial greeting
    if user_input.lower() in ["__init__"]:
        first_name = user.name.split()[0] if user and user.name else "there"
        welcome = (
            f"Hey {first_name}! 👋 I’m Clara, your GMAT prep buddy. "
            "Excited to help you get started on your prep journey!"
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
            break

    onboarding_complete = False

    if parsed_json:
        if key_found == "final_profile":
            onboarding_complete = True

        # ✅ Second-level check
        if key_found == "partial_profile" and parsed_json:
            has_all_fields = all([
                "country" in parsed_json,
                "target_score" in parsed_json,
                "exam_date" in parsed_json,
                "previous_score" in parsed_json
            ])
            if has_all_fields:
                onboarding_complete = True

        # ✅ Persist both final and partial profile fields
        if profile:
            for k, v in parsed_json.items():
                setattr(profile, k, v)
            if onboarding_complete:
                profile.onboarding_complete = True
        else:
            db.add(UserProfile(
                user_id=user_id,
                onboarding_complete=onboarding_complete,
                **parsed_json
            ))
        db.commit()

    cleaned_reply = re.sub(
        r'(partial_profile|final_profile)\s*:\s*\{[^}]*\}\s*', '', reply_text
    ).strip()


    return {
        "reply": cleaned_reply,
        "snippets_used": [m.message for m in memories],
        "onboarding_complete": onboarding_complete
    }
