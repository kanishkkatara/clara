# ================================
# File: src/api/questions.py
# ================================
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.progress import AnswerCreate
from app.schemas.question import (
    QuestionCreate,
    QuestionRead,
    QuestionSummaryRead,
    NextQuestionResponse,
    QuestionResponse
)
from app.services.auth import get_current_user
from app.services.question_service import question_service
from app.services.progress_service import progress_service
from app.services.recommendation_service import recommendation_service

router = APIRouter()

@router.get("/", response_model=List[QuestionSummaryRead])
def list_questions(
    type: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    minDifficulty: Optional[int] = Query(None, alias="minDifficulty"),
    maxDifficulty: Optional[int] = Query(None, alias="maxDifficulty"),
    progress_filter: Optional[str] = Query("all"),  # all | attempted | non-attempted | correct | incorrect
    skip: int = 0,
    limit: int = 20,
    user = Depends(get_current_user),
):
    filters = {
        "type": type or [],
        "tags": tags or [],
        "min_difficulty": minDifficulty,
        "max_difficulty": maxDifficulty,
        "progress_filter": progress_filter,
        "user_id": user.id if user else None,  # only if user authenticated
    }
    return question_service.get_summaries(filters, skip, limit)

@router.get("/{q_id}", response_model=QuestionResponse)
def get_question(
    q_id: UUID,
    include_sub: bool = Query(
        False,
        alias="include_sub",
        description="Include sub-questions if composite"
    ),
):
    try:
        return question_service.get_response(q_id, include_sub)
    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")

@router.post("/", response_model=QuestionRead, status_code=201)
def create_question(payload: QuestionCreate):
    return question_service.create(payload)

@router.post("/{q_id}/submit", response_model=NextQuestionResponse, status_code=status.HTTP_200_OK)
def submit_answer(
    q_id: UUID,
    payload: AnswerCreate,
    session: Session = Depends(get_db),
):
    progress_service.record(payload, session=session)
    next_q = recommendation_service.recommend_next(
        user_id=payload.user_id,
        last_question_id=payload.question_id,
        is_correct=payload.is_correct,
        session=session,
    )
    return NextQuestionResponse(next_question=next_q)

@router.post("/bulk", response_model=List[QuestionRead], status_code=201)
def create_questions_bulk(
    payloads: List[QuestionCreate],
    session: Session = Depends(get_db)
):
    created = question_service.create_bulk(payloads, session)
    return [QuestionRead.from_orm(q) for q in created]

