from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base
from pgvector.sqlalchemy import Vector

class UserMemory(Base):
    __tablename__ = "user_memory"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    message     = Column(String, nullable=False)
    embedding   = Column(Vector(1536), nullable=False)   # adjust dim to your model
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user        = relationship("User", back_populates="memories")
