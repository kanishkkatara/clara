# src/app/services/tutoring_bot.py

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from openai import OpenAI
import os
from sqlalchemy.orm import Session
from app.models.memory import UserMemory

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# — Embedding helper
def get_embedding(text: str) -> List[float]:
    resp = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return resp.data[0].embedding

# — Fetch top‑k similar tutoring memories
def fetch_tutoring_memories(
    db: Session,
    user_id: UUID,
    query_emb: List[float],
    k: int = 5
) -> List[UserMemory]:
    return (
        db.query(UserMemory)
          .filter(UserMemory.user_id == user_id,
                  UserMemory.type == "tutoring")
          .order_by(UserMemory.embedding.l2_distance(query_emb))
          .limit(k)
          .all()
    )

def extract_text(node):
    """
    Given either a string or a dict with:
      - 'text': a simple string, or
      - 'blocks': a list of { 'text': ... } paragraphs
    returns the joined text.
    """
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    # prefer a top-level 'text' field if present
    if 'text' in node and isinstance(node['text'], str):
        return node['text']
    # otherwise, collect from blocks
    blocks = node.get('blocks')
    if isinstance(blocks, list):
        pieces = []
        for b in blocks:
            t = b.get('text')
            if isinstance(t, str):
                pieces.append(t)
        return "\n".join(pieces)
    return ""

# — Build prompt, injecting question context when provided
def build_tutoring_prompt(
    memories: List[UserMemory],
    user_input: str,
    question: Optional[Union[str, Dict[str, Any]]] = None
) -> List[Dict[str, str]]:
    # 1) System intro
    system = (
        "You are Clara, a patient GMAT tutor. "
        "You help students solve questions and clarify concepts, "
        "using step‑by‑step, example‑driven explanations.\n\n"
    )

    # 2) Determine if this is a plain greeting
    is_greet = user_input.strip().lower() in {"hi", "hello", "hey"}

    # 3) If question context is provided and not just a greeting, insert it


    if question and not is_greet:
        # build the prompt
        if isinstance(question, str):
            q_text = question
        else:
            q_text = extract_text(question)

        system += f"Current question:\n\"\"\"\n{q_text}\n\"\"\"\n\n"

        # now options
        opts = question.get("options") if isinstance(question, dict) else None
        if isinstance(opts, list) and opts:
            system += "Options:\n"
            for opt in opts:
                oid = opt.get("id", "")
                # extract text from the same shape
                otext = extract_text(opt)
                system += f"- {oid}: {otext}\n"
            system += "\n"

    # 4) Include past tutoring memory if any
    if memories:
        block = "\n".join(f"- {m.source.upper()}: {m.message}" for m in memories)
        system += f"Recent conversation:\n{block}\n\n"

    # 5) Assemble messages
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_input}
    ]

# — The restored and enhanced handle_tutoring method
async def handle_tutoring(
    db: Session,
    user_id: UUID,
    user_input: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    # A) Persist the user message
    user_emb = get_embedding(user_input)
    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=user_emb,
        type="tutoring",
        source="user"
    ))
    db.commit()

    # B) Extract question context from the incoming dict
    question_ctx: Optional[Union[str, Dict[str, Any]]] = None
    if context:
        # FE should send { "question": { "text": "...", "options": [...] } }
        if "question" in context:
            question_ctx = context["question"]
        # Or it could send a simple string under "question_text"
        elif "question_text" in context:
            question_ctx = context["question_text"]

    # C) Fetch memory & build the prompt
    memories = fetch_tutoring_memories(db, user_id, user_emb)
    prompt = build_tutoring_prompt(memories, user_input, question_ctx)

    # D) Call OpenAI
    resp = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=prompt,
        temperature=0.6
    )
    reply = resp.choices[0].message.content or "Sorry, I didn’t catch that."

    # E) Persist the assistant’s reply
    bot_emb = get_embedding(reply)
    db.add(UserMemory(
        user_id=user_id,
        message=reply,
        embedding=bot_emb,
        type="tutoring",
        source="assistant"
    ))
    db.commit()

    # F) Return the reply and any snippets used
    return {
        "reply": reply,
        "snippets_used": [m.message for m in memories]
    }
