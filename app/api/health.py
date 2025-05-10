# app/routes/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db

router = APIRouter()

@router.get("")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy ({str(e)})"

    return {
        "status": "ok",
        "service": "GMAT Prep API",
        "version": "1.0.0",
        "database": db_status,
    }
