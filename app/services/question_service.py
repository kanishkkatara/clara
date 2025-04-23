from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from app.db import get_db
from app.models.question import Question
from app.schemas.question import QuestionCreate

class QuestionService:
    def get_all(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 50
    ) -> List[Question]:
        db = next(get_db())
        stmt = select(Question)
        if filters.get("type"):
            stmt = stmt.where(Question.type == filters["type"])
        if filters.get("tags"):
            stmt = stmt.where(Question.tags.overlap(filters["tags"]))
        if filters.get("difficulty"):
            stmt = stmt.where(Question.difficulty == filters["difficulty"])
        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt).scalars().all()
        db.close()
        return result

    def get_by_id(self, qid: UUID) -> Question:
        db = next(get_db())
        question = db.get(Question, qid)
        db.close()
        if not question:
            raise KeyError(f"Question {qid} not found")
        return question

    def create(self, payload: QuestionCreate) -> Question:
        db = next(get_db())
        obj = Question(
            type=payload.type,
            content=[block.model_dump() for block in payload.content],
            options=[opt.model_dump() for opt in payload.options],
            answers=payload.answers,
            tags=payload.tags,
            difficulty=payload.difficulty
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        db.close()
        return obj

question_service = QuestionService()
