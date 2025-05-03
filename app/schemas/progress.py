from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel

class AnswerCreate(BaseModel):
    user_id: UUID
    selected_options: Optional[Any] = None
    is_correct: bool
    time_taken:   int