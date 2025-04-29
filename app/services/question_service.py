# ==============================================
# File: src/services/question_service.py
# ==============================================
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from app.db import get_db
from app.models.question import Question
from app.schemas.question import (
    QuestionCreate,
    QuestionSummaryRead,
    QuestionRead,
    CompositeQuestionRead,
    QuestionResponse
)

class QuestionService:
    def get_summaries(
        self, filters: Dict[str, Any], skip: int = 0, limit: int = 50
    ) -> List[QuestionSummaryRead]:
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
        results = db.execute(stmt).scalars().all()
        summaries: List[QuestionSummaryRead] = []
        for q in results:
            # extract first paragraph text as preview
            preview = None
            for block in q.content or []:
                if isinstance(block, dict) and block.get("type") == "paragraph":
                    text = block.get("text", "")
                    preview = text[:100] + ("..." if len(text) > 100 else "")
                    break
            summaries.append(
                QuestionSummaryRead(
                    id=q.id,
                    type=q.type,
                    difficulty=q.difficulty,
                    tags=q.tags,
                    parent_id=q.parent_id,
                    order=q.order,
                    preview_text=preview
                )
            )
        db.close()
        return summaries

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
            options=[opt.model_dump() for opt in payload.options],
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

    def create_bulk(
        self, payloads: List[QuestionCreate], session: Session
    ) -> List[Question]:
        created_objs: List[Question] = []
        current_parent: UUID = None
        for payload in payloads:
            # detect new composite passage
            if payload.type == "multi-source-reasoning":
                obj = Question(
                    type=payload.type,
                    content=[block.model_dump() for block in payload.content],
                    options=[], answers={}, tags=payload.tags,
                    difficulty=payload.difficulty, parent_id=None, order=None
                )
                session.add(obj)
                session.flush()  # assigns obj.id
                current_parent = obj.id
                created_objs.append(obj)
            else:
                # auto-assign parent if not provided
                if payload.parent_id is None and current_parent:
                    payload.parent_id = current_parent
                obj = Question(
                    type=payload.type,
                    content=[block.model_dump() for block in payload.content],
                    options=[opt.model_dump() for opt in payload.options],
                    answers=payload.answers.model_dump(),
                    tags=payload.tags,
                    difficulty=payload.difficulty,
                    parent_id=payload.parent_id,
                    order=payload.order
                )
                session.add(obj)
                created_objs.append(obj)
        session.commit()
        for obj in created_objs:
            session.refresh(obj)
        return created_objs

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
