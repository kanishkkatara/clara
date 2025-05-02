import uuid
from sqlalchemy import Column, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id          = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id     = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role        = Column(String, nullable=False)
    message     = Column(String, nullable=False)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user        = relationship("User", back_populates="chats")
