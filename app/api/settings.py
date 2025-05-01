from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import date

from app.db import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.services.auth import get_current_user

router = APIRouter()

class BasicSettings(BaseModel):
    name: str
    email: EmailStr
    target_score: Optional[int] = None
    exam_date: Optional[date] = None
    previous_score: Optional[int] = None

class DisplaySettings(BaseModel):
    dark_mode: bool

class NotificationSettings(BaseModel):
    notify_mail: bool
    notify_whatsapp: bool

@router.get("/basic", response_model=BasicSettings)
def get_basic(user: User = Depends(get_current_user)):
    p = user.profile
    try:
        exam_date = p.exam_date and date.fromisoformat(p.exam_date)
    except ValueError:
        exam_date = None
    return BasicSettings(
        name=user.name,
        email=user.email,
        target_score=p.target_score,
        exam_date=exam_date,
        previous_score=p.previous_score,
    )

@router.put("/basic")
def update_basic(
    settings: BasicSettings,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # update User
    user.name = settings.name

    # ensure profile exists
    profile = user.profile or UserProfile(user_id=user.id)
    profile.target_score   = settings.target_score
    profile.exam_date      = settings.exam_date.isoformat() if settings.exam_date else None
    profile.previous_score = settings.previous_score
    session.add(user)
    session.add(profile)
    session.commit()
    return {"success": True}

@router.put("/display")
def update_display(
    settings: DisplaySettings,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = user.profile or UserProfile(user_id=user.id)
    profile.dark_mode = settings.dark_mode
    session.add(profile)
    session.commit()
    return {"success": True}

@router.get("/notifications", response_model=NotificationSettings)
def get_notifications(user: User = Depends(get_current_user)):
    p = user.profile
    return NotificationSettings(
        notify_mail     = p.notify_mail,
        notify_whatsapp = p.notify_whatsapp,
    )

@router.put("/notifications")
def update_notifications(
    settings: NotificationSettings,
    session: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    profile = user.profile or UserProfile(user_id=user.id)
    profile.notify_mail     = settings.notify_mail
    profile.notify_whatsapp = settings.notify_whatsapp
    session.add(profile)
    session.commit()
    return {"success": True}
