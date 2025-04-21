# app/services/auth.py
import os
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.models.profile import UserProfile

# load from env
SECRET_KEY      = os.getenv("SECRET_KEY", "your-dev-secret")
ALGORITHM       = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8
GOOGLE_CLIENT_ID= os.getenv("GOOGLE_CLIENT_ID")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    creds_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid auth", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if not user_id:
            raise creds_exc
    except (JWTError, ValueError):
        raise creds_exc

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise creds_exc
    return user
