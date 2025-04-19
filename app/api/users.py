from fastapi import APIRouter
from app.services.user_service import get_user_by_id
from app.models.user import User

router = APIRouter()

@router.get("/{user_id}", response_model=User)
def fetch_user(user_id: int):
    return get_user_by_id(user_id)

@router.post("/", response_model=User)
def create_user(user: User):
    # In a real application, you would save the user to a database
    # Here we just return the user as if it was saved
    return user