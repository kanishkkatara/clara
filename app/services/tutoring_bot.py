from typing import List
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from app.models.memory import UserMemory

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

def fetch_tutoring_memories(db: Session, user_id: int, query_embedding: List[float], k=5):
    return db.query(UserMemory)\
        .filter(UserMemory.user_id == user_id, UserMemory.type == "tutoring")\
        .order_by(UserMemory.embedding.l2_distance(query_embedding))\
        .limit(k).all()

def build_tutor_prompt(memories: List[UserMemory], user_input: str):
    context = "\n".join([f"- {m.message}" for m in memories])
    return [
        {"role": "system", "content": "You are TutorBot helping users improve their test scores."},
        {"role": "system", "content": f"Relevant past context:\n{context}"},
        {"role": "user", "content": user_input}
    ]

async def handle_tutoring(db: Session, user_id: int, user_input: str):
    embedding = get_embedding(user_input)

    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=embedding,
        type="tutoring",
        source="user"
    ))
    db.commit()

    memories = fetch_tutoring_memories(db, user_id, embedding)
    messages = build_tutor_prompt(memories, user_input)

    reply = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    ).choices[0].message.content

    # Save bot reply
    bot_emb = get_embedding(reply)
    db.add(UserMemory(
        user_id=user_id,
        message=reply,
        embedding=bot_emb,
        type="tutoring",
        source="assistant"
    ))
    db.commit()

    return {
        "reply": reply,
        "snippets_used": [m.message for m in memories]
    }
