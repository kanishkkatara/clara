# app/models/payment.py

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, func, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from app.db import Base

class Payment(Base):
    __tablename__ = "payments"

    id                  = Column(
                            PGUUID(as_uuid=True),
                            primary_key=True,
                            default=uuid.uuid4
                          )
    subscription_id     = Column(
                            PGUUID(as_uuid=True),
                            ForeignKey("subscriptions.id", ondelete="CASCADE"),
                            nullable=True,
                            index=True
                          )
    gateway_order_id    = Column(
                            String(128),
                            unique=True,
                            nullable=False,
                            index=True
                          )
    gateway_payment_id  = Column(
                            String(128),
                            unique=True,
                            nullable=True
                          )
    amount_cents        = Column(Integer, nullable=False)
    currency            = Column(String(8), nullable=False, default="INR")
    status              = Column(
                            String(32),
                            nullable=False,
                            default="created",
                            index=True
                          )
    error_code          = Column(String(64), nullable=True)
    raw_payload         = Column(JSONB, nullable=True)
    created_at          = Column(
                            DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False
                          )
    updated_at          = Column(
                            DateTime(timezone=True),
                            server_default=func.now(),
                            onupdate=func.now(),
                            nullable=False
                          )

    # backref from Subscription.payments
    subscription        = relationship("Subscription", back_populates="payments")
