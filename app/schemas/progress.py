from uuid import UUID
from pydantic import BaseModel

class AnswerCreate(BaseModel):
    user_id: UUID
    question_id: UUID
    selected_option: str
    is_correct: bool
