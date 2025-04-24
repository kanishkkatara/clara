# app/api/questions.py

from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Any, Optional
from uuid import UUID
from sqlmodel import Session

from app.db import get_db
from app.schemas.progress import AnswerCreate
from app.schemas.question import (
    NextQuestionResponse,
    QuestionCreate,
    QuestionRead,
    QuestionSummaryRead,
)
from app.services.progress_service import progress_service
from app.services.question_service import question_service

router = APIRouter()

@router.get(
    "/", 
    response_model=List[QuestionSummaryRead],
)
def list_questions(
    type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    difficulty: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
):
    filters = {"type": type, "tags": tags or [], "difficulty": difficulty}
    return question_service.get_all(filters=filters, skip=skip, limit=limit)

@router.get(
    "/{q_id}", 
    response_model=QuestionRead,
)
def get_question(q_id: UUID):
    try:
        return question_service.get_by_id(q_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")

@router.post(
    "/", 
    response_model=QuestionRead,
    status_code=201,
)
def create_question(payload: QuestionCreate):
    return question_service.create(payload)

@router.post(
    "/{q_id}/submit",
    response_model=NextQuestionResponse,
    status_code=status.HTTP_200_OK,
)
def submit_answer(
    q_id: UUID,
    payload: AnswerCreate,
    session: Session = Depends(get_db),
) -> Any:
    print("submit_answer", q_id, payload)
    # 1️⃣ record the answer
    progress_service.record(payload, session=session)

    # 2️⃣ stub‐out next‐question recommender
    next_q = question_service.recommend_next(
        user_id=payload.user_id,
        last_question_id=q_id,
        session=session,
    )

    return NextQuestionResponse(next_question=next_q)
