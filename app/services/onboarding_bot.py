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


def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


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


def extract_updated_fields(text: str) -> Optional[Dict[str, Any]]:
    match = re.search(r'updated_fields\s*:\s*(\{.*?\})', text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def build_onboarding_prompt(memories: List[UserMemory], user_input: str) -> List[Dict[str, str]]:
    memory_blocks = "\n".join(f"{m.source.upper()}: {m.message}" for m in memories)
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    system = (
        "You are Clara, a friendly but very concise onboarding assistant for a GMAT prep app.\n\n"
        "Your job:\n"
        "- Collect these 4 fields naturally: country, target_score, exam_date, previous_score.\n"
        "- NEVER generate long explanations or general facts. Replies should be short, crisp, and conversational.\n"
        "- Assume reasonable values if vague or missing, and proceed without asking again.\n"
        "- Always pick a FUTURE date when assuming exam_date.\n"
        f"- Assume today's date is {today_str}.\n"
        "- Confirm or assume one field per message and include it in the updated_fields block.\n"
        "- updated_fields must include only newly captured or changed fields.\n"
        "- Example:\n"
        "  Sure! I've set your target score to 710. When are you planning to take the test?\n"
        "  updated_fields: {\"target_score\": 710}\n"
        "- Never return partial_profile or final_profile.\n"
        "- Be warm and human.\n\n"
        f"Here’s the chat so far:\n{memory_blocks}"
    )

    messages: List[Dict[str, str]] = [{"role": "system", "content": system}]
    for m in memories:
        messages.append({"role": m.source, "content": m.message})
    messages.append({"role": "user", "content": user_input})
    return messages


async def handle_onboarding(
    db: Session,
    user_id: UUID,
    user_input: str,
    profile_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    user = db.query(User).filter(User.id == user_id).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    updated_fields = {}

    # Update name/email on User if provided
    if profile_data:
        if "name" in profile_data and user:
            user.name = profile_data["name"]
            updated_fields["name"] = user.name
        if "email" in profile_data and user:
            user.email = profile_data["email"]
            updated_fields["email"] = user.email
        db.commit()

        # Persist additional profile fields
        field_map = {
            "country": "country",
            "targetScore": "target_score",
            "examDate": "exam_date",
            "previousScore": "previous_score"
        }
        mapped = {
            field_map[k]: v
            for k, v in profile_data.items()
            if k in field_map and v is not None
        }

        if mapped:
            if profile:
                for attr, value in mapped.items():
                    setattr(profile, attr, value)
                    updated_fields[attr] = value
            else:
                profile = UserProfile(user_id=user_id, **mapped)
                db.add(profile)
                updated_fields.update(mapped)
            db.commit()

    if user_input.lower() == "__init__":
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
            "profile": updated_fields
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

    # Call the LLM
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

    # Parse updated_fields
    parsed_json = extract_updated_fields(reply_text)
    if parsed_json:
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
        for k, v in parsed_json.items():
            setattr(profile, k, v)
            updated_fields[k] = v
        db.commit()

    # Clean reply text
    cleaned = re.sub(r'updated_fields\s*:\s*\{[^}]*\}\s*', '', reply_text).strip()

    return {
        "reply": cleaned,
        "snippets_used": [m.message for m in memories],
        "profile": updated_fields
    }