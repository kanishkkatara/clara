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
from sqlalchemy import and_
from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.orm import joinedload

class QuestionService:

    def get_summaries(
        self, filters: Dict[str, Any], skip: int = 0, limit: int = 50
    ) -> List[QuestionSummaryRead]:
        # Open a DB session
        db = next(get_db())
        user_id = filters.get("user_id")
        pf = filters.get("progress_filter", "all")

        # 1) Base query: top-level questions with children eager-loaded
        query = (
            db.query(Question)
            .options(joinedload(Question.children))
            .filter(Question.parent_id == None)
        )

        # 2) Apply simple filters
        if filters.get("type"):
            query = query.filter(Question.type.in_(filters["type"]))
        if filters.get("tags"):
            query = query.filter(Question.tags.overlap(filters["tags"]))
        if filters.get("min_difficulty") is not None:
            query = query.filter(Question.difficulty >= filters["min_difficulty"])
        if filters.get("max_difficulty") is not None:
            query = query.filter(Question.difficulty <= filters["max_difficulty"])

        # 3) Execute question fetch
        questions = query.all()

        # 4) Load all progress rows for this user at once
        progress_map: Dict[int, List[bool]] = {}
        if user_id:
            rows = (
                db.query(UserQuestionProgress)
                .filter(UserQuestionProgress.user_id == user_id)
                .all()
            )
            for pr in rows:
                progress_map.setdefault(pr.question_id, []).append(pr.is_correct)

        summaries: List[QuestionSummaryRead] = []
        for q in questions:
            # Build preview text
            preview = None
            for block in q.content or []:
                if isinstance(block, dict) and block.get("type") == "paragraph":
                    txt = block.get("text", "")
                    preview = txt[:100] + ("..." if len(txt) > 100 else "")
                    break

            # Determine first subquestion ID
            first_sub = None
            if q.children:
                ordered = sorted(q.children, key=lambda c: (c.order or 0))
                first_sub = ordered[0].id if ordered else None

            # Compute attempted/correct status
            leaf_prog = progress_map.get(q.id, [])
            child_prog = []
            for c in q.children:
                child_prog.extend(progress_map.get(c.id, []))

            attempted = bool(leaf_prog or child_prog)
            if child_prog:
                correct = all(child_prog)
            elif leaf_prog:
                # take the first leaf attempt
                correct = leaf_prog[0]
            else:
                correct = None

            # Apply progress_filter
            if user_id:
                if pf == "non-attempted" and attempted:
                    continue
                if pf == "attempted" and not attempted:
                    continue
                if pf == "correct" and correct is not True:
                    continue
                if pf == "incorrect" and correct is not False:
                    continue

            # Build summary DTO
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
                    first_subquestion_id=first_sub,
                )
            )

        db.close()

        # 5) Paginate in-memory
        return summaries[skip : skip + limit]

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
