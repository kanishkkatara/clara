from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class UserRead(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
    # picture_url: Optional[str]

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
