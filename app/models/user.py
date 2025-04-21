from typing import List, Optional
from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "Student"
    ADMIN = "Admin"

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str
    role: UserRole
    exams: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_active: bool = True

class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    gmat_score: Optional[int] = None
    goals: Optional[str] = None