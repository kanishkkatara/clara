# app/routers/subscriptions.py

from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.services.billing_service import billing_service
from app.schemas.billing import CreateOrderIn, PlanOut, SubscriptionOut, PaymentOut
from app.services.auth import get_current_user

router = APIRouter()

@router.get("/plans", response_model=List[PlanOut])
def list_plans(
    db: Session = Depends(get_db),
) -> List[PlanOut]:
    """List all available subscription plans."""
    return billing_service.list_plans(db)

@router.post("/trial", response_model=SubscriptionOut)
def start_trial(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> SubscriptionOut:
    """Begin a 5-day free trial for the authenticated user."""
    return billing_service.start_trial(current_user, db)

@router.post("/create_order", response_model=PaymentOut)
def create_order(
    payload: CreateOrderIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PaymentOut:
    """Create a payment order for the chosen plan."""
    return billing_service.create_order(payload.plan_id, current_user, db)

@router.post("/webhook")
async def webhook(
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, bool]:
    """Handle Razorpay webhook callbacks."""
    payload = await request.json()
    handled = billing_service.handle_webhook(payload, db)
    if not handled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unhandled or invalid webhook event",
        )
    return {"ok": True}

@router.get("/me", response_model=Optional[SubscriptionOut])
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[SubscriptionOut]:
    """Fetch the current subscription or trial status; returns null if none exists."""
    # Returns None instead of raising 404
    subscription = billing_service.get_my_subscription_optional(current_user, db)
    return subscription
