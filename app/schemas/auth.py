# app/schemas/auth.py
from pydantic import BaseModel

class TokenRequest(BaseModel):
    token: str
