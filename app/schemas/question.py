# src/schemas/question.py

from datetime import datetime
from uuid import UUID
from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

# Base with common Pydantic v2 config (including ORM support)
class PydanticBase(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,         # enable .from_orm()
        json_schema_mode="openapi",
    )

class ContentBlock(PydanticBase):
    type: Literal[
        "paragraph", "image", "table", "list", "dropdown", "numeric"
    ] = Field(..., description="Block type identifier")
    text: Optional[str] = Field(None, description="Paragraph text")
    url: Optional[str] = Field(None, description="Image/Table URL")
    alt: Optional[str] = Field(None, description="Alt text for image")
    headers: Optional[List[str]] = Field(None, description="Table headers")
    rows: Optional[List[List[str]]] = Field(None, description="Table rows")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional block data")

class Option(PydanticBase):
    id: str = Field(..., description="Option identifier, e.g. 'A'")
    blocks: List[ContentBlock] = Field(..., description="Rich content for this option")

class QuestionBase(PydanticBase):
    type: str = Field(..., description="Question type, e.g., 'single_choice'")
    content: List[ContentBlock] = Field(..., description="Rich content blocks")
    options: List[Option] = Field(default_factory=list, description="Answer options")
    answers: Dict[str, Any] = Field(..., description="Correct answer mapping")
    tags: List[str] = Field(default_factory=list, description="Filtering tags")
    difficulty: int = Field(1, ge=1, le=7, description="Difficulty level 1–7")

class QuestionCreate(QuestionBase):
    """Payload for creating a question."""

class QuestionRead(QuestionBase):
    """Schema returned when reading a question from the DB."""
    id: UUID = Field(..., description="Unique question UUID")
    created_at: datetime = Field(..., description="Timestamp of creation")
    updated_at: datetime = Field(..., description="Timestamp of last update")

class NextQuestionResponse(PydanticBase):
    next_question: Optional[QuestionRead] = Field(
        None, description="Recommended next question, if any"
    )

class QuestionSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique question UUID")
    type: str = Field(..., description="Question type")
    difficulty: int = Field(..., description="Difficulty level")
    tags: List[str] = Field(..., description="Question tags")
