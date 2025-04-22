from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id    = Column(Integer, ForeignKey("users.id"), primary_key=True)
    country    = Column(String, nullable=True)
    exam       = Column(String, nullable=True)
    goals      = Column(String, nullable=True)
    onboarding_complete = Column(Boolean, nullable=False, default=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    user       = relationship("User", back_populates="profile")
