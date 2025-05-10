# app/models/subscription.py

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    func,
    ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.db import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    plan_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    status = Column(
        String(32),
        nullable=False,
        index=True
    )
    current_period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    gateway_subscription_id = Column(
        String(128),
        unique=True,
        nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship(
        "Payment",
        back_populates="subscription",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
