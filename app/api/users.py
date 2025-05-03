from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from app.db import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.user import UserRead, Token
from app.services.auth import get_current_user, create_access_token

import os

router = APIRouter()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# -----------------------
# SCHEMAS
# -----------------------
class GoogleAuth(BaseModel):
    id_token: str

class UserUpdate(BaseModel):
    is_onboarded: Optional[bool] = None
    # Add other updatable fields here as needed

# -----------------------
# ROUTES
# -----------------------

@router.get("/me", response_model=UserRead)
def read_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Explicitly include the onboarding flag
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "isOnboarded": current_user.profile.onboarding_complete,
    }


@router.patch("/me", response_model=UserRead)
def update_current_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch associated profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update fields if provided
    if payload.is_onboarded is not None:
        profile.onboarding_complete = payload.is_onboarded
    # TODO: handle additional payload fields

    db.add(profile)
    db.commit()
    db.refresh(profile)
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "isOnboarded": profile.onboarding_complete,
    }


@router.post("/login", response_model=Token)
def login_via_google(auth: GoogleAuth, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            auth.id_token, grequests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    google_id = idinfo["sub"]
    email     = idinfo.get("email")
    name      = idinfo.get("name")
    # picture   = idinfo.get("picture")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            # picture_url=picture
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
