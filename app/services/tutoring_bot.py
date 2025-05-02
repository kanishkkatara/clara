# src/app/services/tutoring_bot.py

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from openai import OpenAI
import os
from sqlalchemy.orm import Session

from app.models.memory import UserMemory
from app.models.question import Question
from app.services.question_service import question_service

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# — Embedding helper
def get_embedding(text: str) -> List[float]:
    resp = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return resp.data[0].embedding


# — Fetch top-k similar tutoring memories
def fetch_tutoring_memories(
    db: Session,
    user_id: UUID,
    query_emb: List[float],
    k: int = 5
) -> List[UserMemory]:
    return (
        db.query(UserMemory)
          .filter(
              UserMemory.user_id == user_id,
              UserMemory.type == "tutoring"
          )
          .order_by(UserMemory.embedding.l2_distance(query_emb))
          .limit(k)
          .all()
    )


def extract_text(node: Any) -> str:
    """
    Given a Question ORM object, a string, or a dict with:
      - 'text': a simple string, or
      - 'blocks': a list of { 'text': ... } paragraphs,
    returns the joined text.
    """
    # unwrap Question ORM
    if isinstance(node, Question):
        # assume .content is a list of blocks
        return "\n".join(extract_text(block) for block in node.content or [])
    # simple string
    if isinstance(node, str):
        return node
    # generic dict shape
    if isinstance(node, dict):
        if 'text' in node and isinstance(node['text'], str):
            return node['text']
        blocks = node.get('blocks')
        if isinstance(blocks, list):
            return "\n".join(
                b.get('text', '') for b in blocks if isinstance(b, dict) and 'text' in b
            )
    return ""


# — Build prompt, injecting question + parent context when provided
def build_tutoring_prompt(
    memories: List[UserMemory],
    user_input: str,
    context: Optional[Dict[str, Question]] = None
) -> List[Dict[str, str]]:
    # 1) System intro
    system = (
        "You are Clara, a patient GMAT tutor. "
        "You help students solve questions and clarify concepts, "
        "using step-by-step, example-driven explanations.\n\n"
    )

    # 2) Plain greeting?
    is_greet = user_input.strip().lower() in {"hi", "hello", "hey"}

    if context and not is_greet:
        q_obj = context.get("question")
        p_obj = context.get("parent")

        # Question text
        if q_obj:
            q_text = extract_text(q_obj)
            system += f"Current question:\n\"\"\"\n{q_text}\n\"\"\"\n\n"
            # Options if present
            opts = getattr(q_obj, "options", None)
            if isinstance(opts, list) and opts:
                system += "Options:\n"
                for opt in opts:
                    # each opt may be dict with id/text
                    oid = opt.get("id", "")
                    otext = extract_text(opt)
                    system += f"- {oid}: {otext}\n"
                system += "\n"

        # Parent question text
        if p_obj:
            p_text = extract_text(p_obj)
            system += f"Related parent question:\n\"\"\"\n{p_text}\n\"\"\"\n\n"

    # 3) Include past tutoring memory
    if memories:
        block = "\n".join(f"- {m.source.upper()}: {m.message}" for m in memories)
        system += f"Recent conversation:\n{block}\n\n"

    # 4) Assemble messages
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_input}
    ]


# — The tutoring handler
async def handle_tutoring(
    db: Session,
    user_id: UUID,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # A) Save the user message
    user_emb = get_embedding(user_input)
    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=user_emb,
        type="tutoring",
        source="user"
    ))
    db.commit()

    # B) Fetch question + parent by ID
    question_ctx: Optional[Dict[str, Question]] = None
    if context and "question" in context:
        q_info = context["question"]
        q_id = q_info.get("id")
        p_id = q_info.get("parent_id")
        q_obj = question_service.get_question_by_id(q_id, session=db) if q_id else None
        p_obj = question_service.get_question_by_id(p_id, session=db) if p_id else None
        question_ctx = {"question": q_obj, "parent": p_obj}

    # C) Build prompt
    memories = fetch_tutoring_memories(db, user_id, user_emb)
    prompt = build_tutoring_prompt(memories, user_input, question_ctx)

    # D) Call OpenAI
    resp = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=prompt,
        temperature=0.6
    )
    reply = resp.choices[0].message.content or "Sorry, I didn’t catch that."

    # E) Save assistant reply
    bot_emb = get_embedding(reply)
    db.add(UserMemory(
        user_id=user_id,
        message=reply,
        embedding=bot_emb,
        type="tutoring",
        source="assistant"
    ))
    db.commit()

    # F) Return
    return {
        "reply": reply,
        "snippets_used": [m.message for m in memories]
    }
