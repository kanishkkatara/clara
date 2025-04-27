# app/services/question_service.py
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models.question import Question
from app.schemas.question import (
    QuestionCreate,
    QuestionRead,
    CompositeQuestionRead,
    QuestionResponse,
)

class QuestionService:
    def get_all(
        self, filters: Dict[str, Any], skip: int = 0, limit: int = 50
    ) -> List[Question]:
        db = next(get_db())
        stmt = select(Question).where(Question.parent_id == None)
        if filters.get("type"):
            stmt = stmt.where(Question.type.in_(filters["type"]))
        if filters.get("tags"):
            stmt = stmt.where(Question.tags.overlap(filters["tags"]))
        if filters.get("min_difficulty") is not None:
            stmt = stmt.where(Question.difficulty >= filters["min_difficulty"])
        if filters.get("max_difficulty") is not None:
            stmt = stmt.where(Question.difficulty <= filters["max_difficulty"])
        stmt = stmt.offset(skip).limit(limit)
        result = db.execute(stmt).scalars().all()
        db.close()
        return result

    def create(self, payload: QuestionCreate) -> Question:
        db = next(get_db())
        obj = Question(
            type=payload.type,
            content=[block.model_dump() for block in payload.content],
            options=[opt.model_dump()   for opt   in payload.options],
            answers=payload.answers.model_dump(),
            tags=payload.tags,
            difficulty=payload.difficulty,
            parent_id=payload.parent_id,
            order=payload.order
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        db.close()
        return obj

    def get_response(
        self, qid: UUID, include_sub: bool = False
    ) -> QuestionResponse:
        db = next(get_db())
        stmt = (
            select(Question)
            .where(Question.id == qid)
            .options(selectinload(Question.children))
        )
        item = db.execute(stmt).scalar_one_or_none()
        if not item:
            db.close()
            raise KeyError(f"Question {qid} not found")

        if include_sub and item.children:
            sub_items = sorted(item.children, key=lambda x: (x.order or 0))
            resp = CompositeQuestionRead(
                groupId=item.id,
                type=item.type,
                passage=item.content,
                subquestions=[QuestionRead.from_orm(child) for child in sub_items],
                totalSubquestions=len(sub_items),
                nextGroupId=None
            )
            db.close()
            return resp

        resp = QuestionRead.from_orm(item)
        db.close()
        return resp

question_service = QuestionService()