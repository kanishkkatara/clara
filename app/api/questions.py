from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from uuid import UUID

from app.schemas.question import QuestionCreate, QuestionRead
from app.services.question_service import question_service

router = APIRouter()

@router.get("/", response_model=List[QuestionRead])
def list_questions(
    type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    difficulty: Optional[int] = None,
    skip: int = 0,
    limit: int = 50
):
    filters = {"type": type, "tags": tags or [], "difficulty": difficulty}
    return question_service.get_all(filters=filters, skip=skip, limit=limit)

@router.get("/{q_id}", response_model=QuestionRead)
def get_question(q_id: UUID):
    try:
        return question_service.get_by_id(q_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")

@router.post("/", response_model=QuestionRead, status_code=201)
def create_question(payload: QuestionCreate):
    return question_service.create(payload)