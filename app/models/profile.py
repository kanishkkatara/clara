# app/models/user_profile.py
import uuid
from sqlalchemy import JSON, Column, Integer, String, Boolean, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.db import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id             = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        primary_key=True,
        default=uuid.uuid4,
    )
    country             = Column(String, nullable=True)
    exam                = Column(String, nullable=True, default="GMAT")
    target_score        = Column(Integer, nullable=True)
    exam_date           = Column(String, nullable=True)
    previous_score      = Column(Integer, nullable=True)
    weekly_hours        = Column(String, nullable=True)
    preferred_times     = Column(JSON, nullable=True)
    onboarding_complete = Column(Boolean, nullable=False, default=False)
    total_time          = Column(Integer, nullable=False, default=0)
    updated_at          = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ─── NEW SETTINGS ─────────────────────────────────────────────────────
    notify_mail         = Column(Boolean, nullable=False, default=False)
    notify_whatsapp     = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="profile")
