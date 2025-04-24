from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.api.users import get_current_user
from app.services.dashboard_service import dashboard_service
from app.schemas.dashboard import DashboardResponse

router = APIRouter()

@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = dashboard_service(db, user)
    return service.get_dashboard()