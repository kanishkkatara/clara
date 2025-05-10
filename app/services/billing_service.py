from typing import List, Optional
import os
from datetime import datetime, timedelta, timezone

import razorpay
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.plan import Plan
from app.models.profile import UserProfile
from app.models.subscription import Subscription
from app.models.user import User

import requests
from cachetools import TTLCache, cached

# 1-hour cache so you don’t hammer the API
_rate_cache = TTLCache(maxsize=10, ttl=43200)

@cached(_rate_cache)
def get_fx_rate(base: str, quote: str) -> float:
    resp = requests.get(
        "https://api.exchangerate.host/latest",
        params={"base": base, "symbols": quote},
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # upstream issue (e.g. 4xx/5xx)
        raise HTTPException(502, f"FX API error: {e}") from e

    data = resp.json()
    rates = data.get("rates")
    print(f"--> FX API response: {data}")
    if not rates or quote not in rates:
        # either wrong endpoint or malformed payload
        raise HTTPException(
            502,
            f"FX API returned unexpected data shape: {data}"
        )

    return rates[quote]

def convert_minor_units(amount_cents: int, from_cur: str, to_cur: str) -> int:
    # rate = get_fx_rate(from_cur, to_cur)
    rate = 84  # TODO: replace with actual rate https://exchangerate.host/
    major = amount_cents / 100.0
    converted_major = major * rate
    # back to smallest unit
    return int(round(converted_major * 100))

class BillingService:
    def __init__(self):
        self.client = razorpay.Client(
            auth=(
                os.getenv("RAZORPAY_KEY_ID", ""),
                os.getenv("RAZORPAY_KEY_SECRET", ""),
            )
        )

    def list_plans(self, db: Session) -> List[Plan]:
        """Return all available pricing plans."""
        return db.query(Plan).order_by(Plan.price_cents).all()

    def start_trial(self, user: User, db: Session) -> Subscription:
        """Create a 5-day free trial for the given user, ensuring one trial per user."""
        previous_trial = (
            db.query(Subscription)
            .filter(
                Subscription.user_id == user.id,
                Subscription.plan_id == None  # null plan_id indicates a trial
            )
            .first()
        )
        if previous_trial:
            raise HTTPException(400, "You have already used your free trial.")

        now = datetime.now(timezone.utc)

        trial = Subscription(
            user_id=user.id,
            plan_id=None,               # signifies a trial
            status="trialing",
            current_period_end=now + timedelta(days=5),
        )
        db.add(trial)
        db.commit()
        db.refresh(trial)
        return trial

    def create_order(self, plan_id: int, user: User, db: Session) -> Payment:
        """Create a Razorpay order and record it in the payments table."""
        plan = db.query(Plan).get(plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found.")
          # ─── fetch country from profile ──────────────────────────────────────────
        # if you’ve set up back_populates on User.profile, you can do:
        country = getattr(user, "profile", None) and user.profile.country
        # fallback to querying manually if not eager-loaded:
        if country is None:
            profile = (
                db.query(UserProfile)
                  .filter(UserProfile.user_id == user.id)
                  .first()
            )
            country = profile.country if profile else None

        currency = "INR" if country and country.lower() in ("india", "in") else "USD"
        if currency == "INR":
            amount = convert_minor_units(plan.price_cents, "USD", currency)
            print(f"--> Converted {plan.price_cents} cents to {amount} {currency}")
        else:
            amount = plan.price_cents
        ts = int(datetime.now(timezone.utc).timestamp())
        user_prefix = str(user.id)[:8]
        plan_prefix = str(plan_id)[:8]
        order_data = {
            "amount": amount,
            "currency": currency,
            "receipt": f"{user_prefix}-{plan_prefix}-{ts}",
        }

        # Create a pending subscription so payment.subscription isn't None
        now = datetime.now(timezone.utc)
        pending_sub = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            status="pending",
            current_period_end=now,  # placeholder until payment succeeds
        )
        db.add(pending_sub)
        db.commit()
        db.refresh(pending_sub)

        razorpay_order = self.client.order.create(order_data)

        payment = Payment(
            subscription_id=pending_sub.id,
            gateway_order_id=razorpay_order["id"],
            amount_cents=amount,
            currency=razorpay_order["currency"],
            status="created",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def handle_webhook(self, payload: dict, db: Session) -> bool:
        """Process a Razorpay webhook payload and update payment/subscription."""
        event = payload.get("event")
        data = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = data.get("order_id")
        payment = db.query(Payment).filter(Payment.gateway_order_id == order_id).first()
        if not payment:
            return True

        if event == "payment.captured":
            payment.gateway_payment_id = data.get("id")
            payment.status = "captured"
            # activate the existing pending subscription
            sub = payment.subscription
            sub.status = "active"
            sub.current_period_end = datetime.now(timezone.utc) + timedelta(days=30)
            db.add(sub)
        elif event == "payment.failed":
            payment.status = "failed"
        payment.raw_payload = payload
        db.commit()
        return True

    def get_my_subscription_optional(
        self, user: User, db: Session
    ) -> Optional[Subscription]:
        """Return the latest subscription (trial or paid) or None if not found."""
        return (
            db.query(Subscription)
              .filter(Subscription.user_id == user.id)
              .order_by(Subscription.current_period_end.desc())
              .first()
        )

# Singleton instance for router imports
billing_service = BillingService()
