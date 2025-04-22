from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db import Base

class UserMemory(Base):
    __tablename__ = "user_memory"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    message    = Column(String, nullable=False)
    embedding  = Column(Vector(1536), nullable=False)
    type       = Column(String, nullable=True)  # onboarding, tutoring, etc.
    source     = Column(String, nullable=True)  # user, assistant
    importance = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user       = relationship("User", back_populates="memories")
