# File: app/schemas/payment.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from enum import Enum

class BillingInterval(str, Enum):
    month = 'month'
    semiannual = 'semiannual'
    annual = 'annual'

class PlanOut(BaseModel):
    id: UUID
    name: str
    price_cents: int
    strike_price_cents: int
    billing_interval: BillingInterval
    created_at: datetime

class SubscriptionOut(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: Optional[UUID]
    status: str
    current_period_end: datetime

class PaymentOut(BaseModel):
    id: UUID
    subscription_id: Optional[UUID]
    gateway_order_id: Optional[str]
    gateway_payment_id: Optional[str]
    amount_cents: int
    currency: str
    status: str
    error_code: Optional[str]
    raw_payload: Optional[dict]
    created_at: datetime
    updated_at: datetime

class CreateOrderIn(BaseModel):
    plan_id: UUID