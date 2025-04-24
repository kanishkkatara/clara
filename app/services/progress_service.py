# app/services/progress_service.py

from sqlalchemy.orm import Session
from app.models.progress import UserQuestionProgress
from app.schemas.progress import AnswerCreate

class ProgressService:
    def record(self, payload: AnswerCreate, session: Session) -> UserQuestionProgress:
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
