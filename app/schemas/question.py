# src/schemas/question.py

from datetime import datetime
from uuid import UUID
from typing import Dict, List, Literal, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- Shared base enabling .from_orm() and OpenAPI mode ---
class PydanticBase(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_schema_mode="openapi",
    )

# --- Rich content blocks ---
class Hotspot(PydanticBase):
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    option_id: str = Field(...)

class ContentBlock(PydanticBase):
    type: Literal[
        "paragraph", "image", "table", "list",
        "dropdown", "numeric", "matrix", "ds_grid"
    ] = Field(...)
    text:    Optional[str] = None
    url:     Optional[str] = None
    alt:     Optional[str] = None
    headers: Optional[List[str]] = None
    rows:    Optional[List[List[str]]] = None
    data:    Optional[Dict[str, Any]] = None

    @field_validator("alt", mode="before")
    def require_alt_on_images(cls, v, info):
        # only enforce alt text on actual image blocks
        if info.data.get("type") == "image" and not v:
            raise ValueError("`alt` text is required for image blocks")
        return v
# --- Options for multiple-choice items ---
class Option(PydanticBase):
    id:     str              = Field(..., description="Option label, e.g. 'A'")
    blocks: List[ContentBlock] = Field(..., description="Rich content for this option")

# --- The single-question answer schema ---
class AnswerSchema(PydanticBase):
    correct_option_id: Optional[str]                = None
    selected_choice_index: Optional[int]            = None
    selected_pairs: Optional[List[Dict[str,int]]]   = None
    clicked_hotspot_id: Optional[str]               = None

# --- Base fields shared by create & read ---
class QuestionBase(PydanticBase):
    type:       str                  = Field(..., description="e.g. 'problem-solving'")
    content:    List[ContentBlock]   = Field(..., description="Stem & media blocks")
    options:    List[Option]         = Field(default_factory=list)
    answers:    AnswerSchema         = Field(..., description="Correct-answer payload")
    tags:       List[str]            = Field(default_factory=list)
    difficulty: int                  = Field(1, ge=1, le=7)

# --- Payload when inserting a question ---
class QuestionCreate(QuestionBase):
    parent_id: Optional[UUID] = Field(None, description="For sub-questions")
    order:     Optional[int]   = Field(None, description="Position within group")

# --- Single question returned from GET, discriminated by kind="single" ---
class QuestionRead(QuestionBase):
    kind:       Literal["single"] = Field("single", alias="kind")
    id:         UUID
    created_at: datetime
    updated_at: datetime

# --- Composite (multi-sub-question) bundle returned from GET with include_sub=true ---
class CompositeQuestionRead(PydanticBase):
    kind:               Literal["composite"]     = Field("composite", alias="kind")
    group_id:           UUID                    = Field(..., alias="groupId")
    type:               str
    passage:            List[ContentBlock]
    subquestions:       List[QuestionRead]
    total_subquestions: int                     = Field(..., alias="totalSubquestions")
    next_group_id:      Optional[UUID]          = Field(None, alias="nextGroupId")

# --- A single summary for listing endpoints ---
class QuestionSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:         UUID
    type:       str
    difficulty: int
    tags:       List[str]
    parent_id: Optional[UUID] = Field(None, alias="parentId")
    order:     Optional[int]   = None

# --- Union for GET /questions/{id} responses ---
QuestionResponse = Union[QuestionRead, CompositeQuestionRead]

# --- What we return from POST /questions/{id}/submit ---
class NextQuestionResponse(PydanticBase):
    next_question: Optional[QuestionResponse] = Field(None)
