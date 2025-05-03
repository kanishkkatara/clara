# app/services/progress_service.py

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.profile import UserProfile
from app.models.progress import UserQuestionProgress
from app.schemas.progress import AnswerCreate

class ProgressService:
    def record(self, question_id: str, payload: AnswerCreate, session: Session) -> UserQuestionProgress:
        existing = (
            session.query(UserQuestionProgress)
                   .filter_by(
                       user_id=payload.user_id,
                       question_id=question_id
                   )
                   .one_or_none()
        )

        if existing:
            # 2a) Update the existing entry
            existing.is_correct = payload.is_correct
            existing.selected_options = payload.selected_options
            existing.answered_at = datetime.utcnow()
            existing.time_taken  = payload.time_taken
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        # 2b) Otherwise, create a new record
        prog = UserQuestionProgress(
            user_id=payload.user_id,
            question_id=question_id,
            is_correct=payload.is_correct,
            selected_options=payload.selected_options,
            time_taken=   payload.time_taken 
        )
        session.add(prog)
        session.commit()
        session.refresh(prog)
        profile = session.query(UserProfile).filter_by(user_id=payload.user_id).one()
        profile.total_time += payload.time_taken
        session.add(profile)
        session.commit()
        return prog
progress_service = ProgressService()
