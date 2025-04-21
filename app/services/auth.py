# app/services/auth.py
import os
from fastapi import HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

def handle_google_login(payload):
    try:
        idinfo = id_token.verify_oauth2_token(payload.token, grequests.Request(), GOOGLE_CLIENT_ID)
        email = idinfo.get("email")
        name = idinfo.get("name")
        google_id = idinfo.get("sub")

        # Insert/find user in DB here, then return JWT
        return {"token": "your-app-jwt-token"}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")
