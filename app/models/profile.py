import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id    = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), primary_key=True, default=uuid.uuid4)
    country    = Column(String, nullable=True)
    exam       = Column(String, nullable=True)
    goals      = Column(String, nullable=True)
    onboarding_complete = Column(Boolean, nullable=False, default=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user       = relationship("User", back_populates="profile")
