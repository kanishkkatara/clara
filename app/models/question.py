# =====================================
# File: app/models/question.py
# =====================================
import uuid
from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship
from app.db import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(PGUUID(as_uuid=True), ForeignKey("questions.id"), nullable=True, index=True)
    order = Column(Integer, nullable=True)
    type = Column(String, nullable=False, index=True)
    content = Column(JSON, nullable=False, server_default="[]")
    options = Column(JSON, nullable=False, server_default="[]")
    answers = Column(JSON, nullable=False, server_default="{}")
    tags = Column(ARRAY(String), nullable=False, server_default="{}")
    difficulty = Column(Integer, nullable=False, server_default="1")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    source = Column(String, nullable=True)

    children = relationship("Question", back_populates="parent", lazy="selectin", order_by="Question.order")
    parent = relationship("Question", back_populates="children", remote_side=[id])
    progress = relationship("UserQuestionProgress", back_populates="question")
