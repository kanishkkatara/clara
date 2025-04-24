import uuid
from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from app.db import Base
from sqlalchemy.orm import relationship

class Question(Base):
    __tablename__ = "questions"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        unique=True
    )
    type = Column(
        String,
        nullable=False,
        index=True
    )
    content = Column(
        JSON,
        nullable=False,
        server_default="[]"
    )
    options = Column(
        JSON,
        nullable=False,
        server_default="[]"
    )
    answers = Column(
        JSON,
        nullable=False,
        server_default="{}"
    )
    tags = Column(
        ARRAY(String),
        nullable=False,
        server_default="{}"
    )
    difficulty = Column(
        Integer,
        nullable=False,
        server_default="1"
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
    progress = relationship("UserQuestionProgress", back_populates="question")