import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db import Base

class UserMemory(Base):
    __tablename__ = "user_memory"

    id         = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message    = Column(String, nullable=False)
    embedding  = Column(Vector(1536), nullable=False)
    type       = Column(String, nullable=True)
    source     = Column(String, nullable=True)
    importance = Column(Integer, default=1)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user       = relationship("User", back_populates="memories")
