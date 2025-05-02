# src/app/services/tutoring_bot.py

from typing import Any, Dict, List, Optional
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
    if isinstance(node, Question):
        return "\n".join(extract_text(block) for block in node.content or [])
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        if 'text' in node and isinstance(node['text'], str):
            return node['text']
        blocks = node.get('blocks')
        if isinstance(blocks, list):
            return "\n".join(
                b.get('text', '') for b in blocks
                if isinstance(b, dict) and 'text' in b
            )
    return ""


# — Build prompt, injecting question + parent context when provided
def build_tutoring_prompt(
    memories: List[UserMemory],
    user_input: str,
    context: Optional[Dict[str, Question]] = None
) -> List[Dict[str, str]]:
    system = (
        "You are Clara, a patient GMAT tutor. "
        "You help students solve questions and clarify concepts, "
        "using step-by-step, example-driven explanations.\n\n"
    )

    is_greet = user_input.strip().lower() in {"hi", "hello", "hey"}

    if context and not is_greet:
        q_obj = context.get("question")
        p_obj = context.get("parent")

        if q_obj:
            q_text = extract_text(q_obj)
            system += f"Current question:\n\"\"\"\n{q_text}\n\"\"\"\n\n"
            opts = getattr(q_obj, "options", None)
            if isinstance(opts, list) and opts:
                system += "Options:\n"
                for opt in opts:
                    oid = opt.get("id", "")
                    otext = extract_text(opt)
                    system += f"- {oid}: {otext}\n"
                system += "\n"

        if p_obj:
            p_text = extract_text(p_obj)
            system += f"Related parent question:\n\"\"\"\n{p_text}\n\"\"\"\n\n"

    if memories:
        convo = "\n".join(f"- {m.source.upper()}: {m.message}" for m in memories)
        system += f"Recent conversation:\n{convo}\n\n"

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
    # A) Save the user’s message
    user_emb = get_embedding(user_input)
    db.add(UserMemory(
        user_id=user_id,
        message=user_input,
        embedding=user_emb,
        type="tutoring",
        source="user"
    ))
    db.commit()

    # B) Load question + parent from context
    q_obj: Optional[Question] = None
    p_obj: Optional[Question] = None
    if context and "question" in context:
        info = context["question"]
        if info.get("id"):
            q_obj = question_service.get_question_by_id(info["id"], session=db)
        if info.get("parent_id"):
            p_obj = question_service.get_question_by_id(info["parent_id"], session=db)

    # Prepare to collect snippet texts
    snippets_used: List[str] = []

    # C) Check for cached explanation
    if user_input.strip().lower().startswith("please explain") and q_obj and q_obj.explanation:
        reply = q_obj.explanation
    else:
        # D) Retrieve full UserMemory objects and build the prompt
        memories = fetch_tutoring_memories(db, user_id, user_emb)
        snippets_used = [m.message for m in memories]

        prompt = build_tutoring_prompt(
            memories=memories,
            user_input=user_input,
            context={"question": q_obj, "parent": p_obj}
        )

        # E) Call OpenAI
        resp = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=prompt,
            temperature=0.6
        )
        reply = resp.choices[0].message.content or "Sorry, I didn’t catch that."

        # F) Cache new explanation if asked
        if user_input.strip().lower().startswith("please explain") and q_obj:
            q_obj.explanation = reply
            db.add(q_obj)

    # G) Save the assistant reply and commit everything
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
        "snippets_used": snippets_used
    }
