# app/services/progress_service.py

import datetime
from sqlalchemy.orm import Session
from app.models.progress import UserQuestionProgress
from app.schemas.progress import AnswerCreate

class ProgressService:
    def record(self, payload: AnswerCreate, session: Session) -> UserQuestionProgress:
        existing = (
            session.query(UserQuestionProgress)
                   .filter_by(
                       user_id=payload.user_id,
                       question_id=payload.question_id
                   )
                   .one_or_none()
        )

        if existing:
            # 2a) Update the existing entry
            existing.is_correct = payload.is_correct
            # bump answered_at to now (you could also let the DB default it)
            existing.answered_at = datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        # 2b) Otherwise, create a new record
        prog = UserQuestionProgress(
            user_id=payload.user_id,
            question_id=payload.question_id,
            is_correct=payload.is_correct,
        )
        session.add(prog)
        session.commit()
        session.refresh(prog)
        return prog
progress_service = ProgressService()
