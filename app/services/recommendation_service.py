# app/services/recommendation_service.py

from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.question import Question
from app.models.progress import UserQuestionProgress
from app.schemas.question import QuestionRead

class RecommendationService:
    def recommend_next(
        self,
        user_id: UUID,
        last_question_id: UUID,
        is_correct: bool,
        session: Session,
    ) -> Optional[QuestionRead]:
        # 1) Fetch the last question
        last_q = session.query(Question).get(last_question_id)
        if not last_q:
            return None

        tags = last_q.tags or []
        diff = last_q.difficulty or 1

        # 2) Build a base query excluding answered questions
        answered = (
            session.query(UserQuestionProgress.question_id)
            .filter(UserQuestionProgress.user_id == user_id)
        )

        # ➤ New: which IDs are actually parents of others?
        child_parents = (
            session.query(Question.parent_id)
            .filter(Question.parent_id != None)
        )

        # 3) Base: exclude answered _and_ exclude any parent questions
        base_q = (
            session.query(Question)
            .filter(
                ~Question.id.in_(answered),
                ~Question.id.in_(child_parents)
            )
        )

        candidate = None

        if not is_correct:
            # 3a) Reinforce same difficulty + same tags
            candidate = (
                base_q
                .filter(Question.difficulty == diff, Question.tags.overlap(tags))
                .order_by(func.random())
                .first()
            )
        else:
            # 3b) If correct, try next-difficulty in same tags
            candidate = (
                base_q
                .filter(Question.difficulty > diff, Question.tags.overlap(tags))
                .order_by(Question.difficulty.asc(), func.random())
                .first()
            )
            # 3c) Fallback to same difficulty (any topic)
            if not candidate:
                candidate = (
                    base_q
                    .filter(Question.difficulty == diff)
                    .order_by(func.random())
                    .first()
                )

        # 4) Final fallback to any unanswered question
        if not candidate:
            candidate = base_q.order_by(func.random()).first()

        # 5) Return as your Pydantic schema
        return QuestionRead.from_orm(candidate) if candidate else None


recommendation_service = RecommendationService()
