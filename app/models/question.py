# app/models/question.py
import uuid
from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import relationship
from app.db import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        unique=True
    )
    parent_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("questions.id"),
        nullable=True,
        index=True
    )
    order = Column(
        Integer,
        nullable=True,
        comment="Order within composite group"
    )

    type = Column(
        String,
        nullable=False,
        index=True
    )
    content = Column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="List of ContentBlock dicts"
    )
    options = Column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="List of Option dicts"
    )
    answers = Column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Map of sub-question ID to answer schema"
    )
    tags = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}",
        comment="List of tags for filtering"
    )
    difficulty = Column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Difficulty level 1-7"
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Composite relationships
    children = relationship(
        "Question",
        back_populates="parent",
        lazy="selectin",
        order_by="Question.order"
    )
    parent = relationship(
        "Question",
        back_populates="children",
        remote_side=[id]
    )

    progress = relationship("UserQuestionProgress", back_populates="question")