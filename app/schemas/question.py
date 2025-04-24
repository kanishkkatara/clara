from datetime import datetime
from uuid import UUID
from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

# from app.schemas.progress import ProgressRead

class PydanticBase(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_mode="openapi"
    )

class ContentBlock(PydanticBase):
    type: Literal[
        "paragraph", "image", "table", "list", "dropdown", "numeric"
    ] = Field(..., description="Block type identifier")
    text: Optional[str] = None
    url: Optional[str] = None
    alt: Optional[str] = None
    headers: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    data: Optional[Dict[str, Any]] = None

class Option(PydanticBase):
    id: str
    blocks: List[ContentBlock]

class QuestionBase(PydanticBase):
    type: str = Field(..., description="Question type, e.g., single_choice")
    content: List[ContentBlock] = Field(..., description="Rich content blocks")
    options: List[Option] = Field(default_factory=list, description="Answer options blocks")
    answers: Dict[str, Any] = Field(..., description="Correct answer mapping")
    tags: List[str] = Field(default_factory=list, description="Filtering tags")
    difficulty: int = Field(1, ge=1, le=7, description="Difficulty level 1-7")

class QuestionCreate(QuestionBase):
    pass

class QuestionRead(QuestionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

class NextQuestionResponse(BaseModel):
    next_question: Optional[QuestionRead] = None

class QuestionSummaryRead(BaseModel):
    id: UUID
    type: str
    difficulty: int
    tags: List[str]

    class Config:
        orm_mode = True
