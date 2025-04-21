# app/routes/auth.py
from fastapi import APIRouter, HTTPException
from app.schemas.auth import TokenRequest
from app.services.auth import handle_google_login

router = APIRouter()

@router.post("/api/auth/google")
def google_login(payload: TokenRequest):
    return handle_google_login(payload)
