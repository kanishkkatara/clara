from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class ChatLog(Base):
    __tablename__ = "chat_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    role        = Column(String, nullable=False)   # "user" or "bot"
    message     = Column(String, nullable=False)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user        = relationship("User", back_populates="chats")
