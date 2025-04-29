# app/models/progress.py

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db import Base

class UserQuestionProgress(Base):
    __tablename__ = "user_question_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    time_taken   = Column(Integer, nullable=False, default=0)

    # back-references:
    user = relationship("User", back_populates="progress")
    question = relationship("Question", back_populates="progress")
