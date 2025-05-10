import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, func
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    google_id     = Column(String, unique=True, index=True, nullable=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    name          = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True),
                           server_default=func.now(),
                           onupdate=func.now())
    progress = relationship("UserQuestionProgress", back_populates="user")

    profile       = relationship("UserProfile", back_populates="user", uselist=False)
    memories      = relationship("UserMemory", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")

