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

        # 2) If it's a composite child, delegate to composite handler
        if last_q.parent_id is not None:
            return self._recommend_composite(user_id, last_q, session)

        # 3) Handle simple question logic
        last_type = last_q.type
        last_diff = last_q.difficulty or 1

        # Fetch answered question IDs
        answered = session.query(UserQuestionProgress.question_id).filter(
            UserQuestionProgress.user_id == user_id
        )
        answered_ids = [qid for (qid,) in answered]

        # Exclude composite parents
        child_parents = session.query(Question.parent_id).filter(Question.parent_id != None)

        base_q = session.query(Question).filter(
            ~Question.id.in_(answered_ids),
            ~Question.id.in_(child_parents),
            Question.type == last_type,
        )

        candidate = None

        if not is_correct:
            candidate = (
                base_q.filter(Question.difficulty == last_diff)
                .order_by(func.random())
                .first()
            )
        else:
            candidate = (
                base_q.filter(Question.difficulty > last_diff)
                .order_by(Question.difficulty.asc(), func.random())
                .first()
            )
            if not candidate:
                candidate = (
                    base_q.filter(Question.difficulty == last_diff)
                    .order_by(func.random())
                    .first()
                )

        if not candidate:
            candidate = base_q.order_by(func.random()).first()

        return QuestionRead.from_orm(candidate) if candidate else None

    def _recommend_composite(
        self,
        user_id: UUID,
        last_q: Question,
        session: Session
    ) -> Optional[QuestionRead]:
        # Use parent ID to identify the composite set
        parent_id = last_q.parent_id

        # Get all children of the current parent in order
        children = session.query(Question).filter(
            Question.parent_id == parent_id
        ).order_by(Question.order).all()

        # Fetch all answered question IDs once
        answered_ids = {
            qid for (qid,) in session.query(UserQuestionProgress.question_id)
            .filter(UserQuestionProgress.user_id == user_id)
            .all()
        }

        # Serve next unanswered child
        for child in children:
            if child.id not in answered_ids:
                return QuestionRead.from_orm(child)

        # All children completed → move to next composite parent
        all_parents = session.query(Question).filter(
            Question.parent_id == None,
            Question.type == session.query(Question).get(parent_id).type
        ).all()

        attempted_parent_ids = []
        for parent in all_parents:
            composite_children = session.query(Question).filter(
                Question.parent_id == parent.id
            ).all()
            if all(child.id in answered_ids for child in composite_children):
                attempted_parent_ids.append(parent.id)

        # Find next parent not fully attempted
        next_parent = (
            session.query(Question)
            .filter(
                Question.parent_id == None,
                Question.type == session.query(Question).get(parent_id).type,
                ~Question.id.in_(attempted_parent_ids),
                Question.id != parent_id
            )
            .order_by(func.random())
            .first()
        )

        if next_parent:
            first_child = (
                session.query(Question)
                .filter(Question.parent_id == next_parent.id)
                .order_by(Question.order)
                .first()
            )
            if first_child:
                return QuestionRead.from_orm(first_child)

        return None


recommendation_service = RecommendationService()
