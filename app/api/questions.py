from fastapi import APIRouter, Query
from app.services.question_service import get_questions, get_question_by_id
from app.models.question import Question
from typing import List

router = APIRouter()

@router.get("/", response_model=List[Question])
def fetch_questions(tags: List[str] = Query([])):
    return get_questions(tags)

@router.get("/{question_id}", response_model=Question)
def fetch_question_by_id(question_id: int):
    return get_question_by_id(question_id)

@router.post("/", response_model=Question)
def create_question(question: Question):
    return question
