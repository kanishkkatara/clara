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
    IsDeletedPayload,
    NextQuestionIdResponse,
    QuestionCreate,
    QuestionRead,
    QuestionSummaryRead,
    QuestionResponse,
    SingleQuestionRead,
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
    session: Session = Depends(get_db)
):
    try:
        question = question_service.get_question_by_id(q_id, session=session)

        # --- CASE 1: Subquestion inside composite ---
        if question.parent_id:
            parent_q = question_service.get_question_by_id(question.parent_id, session=session)

            return SingleQuestionRead(
                kind="single",
                id=question.id,
                type=question.type,
                content=question.content,
                options=question.options,
                answers=question.answers,
                tags=question.tags,
                difficulty=question.difficulty,
                order=question.order or 0,
                parent_id=question.parent_id,
                created_at=question.created_at,
                updated_at=question.updated_at,
                parent=parent_q
            )

        # --- CASE 2: Standalone question ---
        return SingleQuestionRead(
            kind="single",
            id=question.id,
            type=question.type,
            content=question.content,
            options=question.options,
            answers=question.answers,
            tags=question.tags,
            difficulty=question.difficulty,
            order=question.order or 0,
            parent_id=question.parent_id,
            created_at=question.created_at,
            updated_at=question.updated_at,
            parent=None
        )

    except KeyError:
        raise HTTPException(status_code=404, detail="Question not found")

@router.post("/{q_id}/submit", response_model=NextQuestionIdResponse, status_code=status.HTTP_200_OK)
def submit_answer(
    q_id: UUID,
    payload: AnswerCreate,
    session: Session = Depends(get_db),
):
    progress_service.record(payload, session=session)

    # Fetch the current question to check if it is part of a composite
    current_q = question_service.get_question_by_id(payload.question_id, session=session)

    next_question = None

    if current_q.parent_id:
        # 🧠 Current question is a subquestion inside a composite group
        subquestions = question_service.get_subquestions_by_group(current_q.parent_id, session=session)
        subquestions = sorted(subquestions, key=lambda q: q.order)

        current_index = next((i for i, q in enumerate(subquestions) if q.id == current_q.id), -1)

        if 0 <= current_index < len(subquestions) - 1:
            # ➡ There is a next subquestion in the same composite group
            next_question = subquestions[current_index + 1]

    # If no next subquestion found, recommend a fresh question
    if not next_question:
        next_question = recommendation_service.recommend_next(
            user_id=payload.user_id,
            last_question_id=payload.question_id,
            is_correct=payload.is_correct,
            session=session,
        )

    return NextQuestionIdResponse(next_question_id=next_question.id if next_question else None)

@router.post("/", response_model=QuestionRead, status_code=201)
def create_question(payload: QuestionCreate):
    return question_service.create(payload)

@router.post("/bulk", response_model=List[QuestionRead], status_code=201)
def create_questions_bulk(
    payloads: List[QuestionCreate],
    session: Session = Depends(get_db)
):
    created = question_service.create_bulk(payloads, session)
    return [QuestionRead.from_orm(q) for q in created]

@router.patch(
    "/{q_id}/isdeleted",
    response_model=SingleQuestionRead,
    summary="Toggle the isdeleted flag on a question",
)
def update_question_isdeleted(
    q_id: UUID,
    payload: IsDeletedPayload,
    session: Session = Depends(get_db),
):
    # fetch or 404
    question = question_service.get_question_by_id(q_id, session=session)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # update flag
    question.is_deleted = payload.is_deleted
    session.add(question)
    session.commit()
    session.refresh(question)

    return question