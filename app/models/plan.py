# app/models/plan.py

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base
from sqlalchemy.dialects.postgresql import UUID as PGUUID

class Plan(Base):
    __tablename__ = "plans"

    id                  = Column(
                            PGUUID(as_uuid=True),
                            primary_key=True,
                            default=uuid.uuid4
                          )
    name                = Column(String(32), unique=True, nullable=False)
    price_cents         = Column(Integer, nullable=False)
    strike_price_cents  = Column(Integer, nullable=False)
    billing_interval    = Column(String(16), nullable=False, index=True)
    created_at          = Column(
                            DateTime(timezone=True),
                            server_default=func.now(),
                            nullable=False
                          )

    subscriptions       = relationship(
                            "Subscription",
                            back_populates="plan"
                          )
