# ==============================================
# File: src/services/question_service.py
# ==============================================
from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.question import Question
from app.models.progress import UserQuestionProgress
from app.schemas.question import (
    QuestionCreate,
    QuestionSummaryRead
)

class QuestionService:
    def get_summaries(
        self, filters: Dict[str, Any], skip: int = 0, limit: int = 50
    ) -> List[QuestionSummaryRead]:
        db = next(get_db())

        user_id = filters.get("user_id")

        stmt = select(
            Question,
        )

        if user_id:
            stmt = stmt.add_columns(UserQuestionProgress.is_correct)

        stmt = stmt.where(Question.parent_id == None)

        # Question filters
        if filters.get("type"):
            stmt = stmt.where(Question.type.in_(filters["type"]))
        if filters.get("tags"):
            stmt = stmt.where(Question.tags.overlap(filters["tags"]))
        if filters.get("min_difficulty") is not None:
            stmt = stmt.where(Question.difficulty >= filters["min_difficulty"])
        if filters.get("max_difficulty") is not None:
            stmt = stmt.where(Question.difficulty <= filters["max_difficulty"])

        # Join progress ONLY if user_id is present
        if user_id:
            stmt = stmt.outerjoin(
                UserQuestionProgress,
                (UserQuestionProgress.question_id == Question.id) &
                (UserQuestionProgress.user_id == user_id)
            )

            # Progress filters
            pf = filters.get("progress_filter", "all")
            if pf == "attempted":
                stmt = stmt.where(UserQuestionProgress.is_correct.isnot(None))
            elif pf == "non-attempted":
                stmt = stmt.where(UserQuestionProgress.is_correct.is_(None))
            elif pf == "correct":
                stmt = stmt.where(UserQuestionProgress.is_correct == True)
            elif pf == "incorrect":
                stmt = stmt.where(UserQuestionProgress.is_correct == False)

        stmt = stmt.offset(skip).limit(limit)

        results = db.execute(stmt).all()

        summaries: List[QuestionSummaryRead] = []

        for row in results:
            if user_id:
                q, is_correct = row
                attempted = is_correct is not None
                correct = is_correct if attempted else None
            else:
                q = row[0]  # only Question, no is_correct
                attempted = False
                correct = None

            preview = None
            for block in q.content or []:
                if isinstance(block, dict) and block.get("type") == "paragraph":
                    text = block.get("text", "")
                    preview = text[:100] + ("..." if len(text) > 100 else "")
                    break

            # 🧠 Fetch first subquestion ID if composite (parent_id == None but has children)
            first_sub_id = None
            if q.children:
                # Sort children by order and pick the first
                ordered_subs = sorted(q.children, key=lambda c: (c.order or 0))
                if ordered_subs:
                    first_sub_id = ordered_subs[0].id

            summaries.append(
                QuestionSummaryRead(
                    id=q.id,
                    type=q.type,
                    difficulty=q.difficulty,
                    tags=q.tags,
                    parent_id=q.parent_id,
                    order=q.order,
                    preview_text=preview,
                    attempted=attempted,
                    correct=correct,
                    first_subquestion_id=first_sub_id  # ✅ new field
                )
            )

        db.close()
        return summaries

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
            order=payload.order,
            source=payload.source
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

        # Define which types are considered composite parents
        COMPOSITE_TYPES = {"multi-source-reasoning", "reading-comprehension"}

        current_parent: UUID = None

        for payload in payloads:
            # If this is a composite type, create a new parent question
            if payload.type in COMPOSITE_TYPES:
                obj = Question(
                    type=payload.type,
                    content=[block.model_dump() for block in payload.content],
                    options=[],  # Composite parents have no options
                    answers={},  # Composite parents have no answers
                    tags=payload.tags,
                    difficulty=payload.difficulty,
                    parent_id=None,
                    order=None,
                    source=payload.source
                )
                session.add(obj)
                session.flush()  # Assigns obj.id
                current_parent = obj.id
                created_objs.append(obj)

            else:
                # If no parent_id provided, assign the last created composite parent
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
                    order=payload.order,
                    source=payload.source
                )
                session.add(obj)
                created_objs.append(obj)

        session.commit()

        # Refresh to load the final state from the DB
        for obj in created_objs:
            session.refresh(obj)

        return created_objs

    def get_question_by_id(self, qid: UUID, session: Session) -> Question:
        stmt = select(Question).where(Question.id == qid)
        result = session.execute(stmt).scalar_one_or_none()
        if not result:
            raise KeyError(f"Question {qid} not found")
        return result

    def get_subquestions_by_group(self, group_id: UUID, session: Session) -> List[Question]:
        stmt = (
            select(Question)
            .where(Question.parent_id == group_id)
        )
        results = session.execute(stmt).scalars().all()
        return results

question_service = QuestionService()
