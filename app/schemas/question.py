# ================================
# File: src/schemas/question.py
# ================================
from datetime import datetime
from uuid import UUID
from typing import List, Literal, Optional, Union, Dict, Any
from typing_extensions import Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator

# --- Shared base for ORM-friendly models ---
class PydanticBase(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        json_schema_mode="openapi",
    )

# --- Content block models (discriminated by `type`) ---
class ParagraphBlock(PydanticBase):
    type: Literal["paragraph"]
    text: str
    data: Optional[Dict[str, Any]] = None

class ImageBlock(PydanticBase):
    type: Literal["image"]
    url: str
    alt: str
    data: Optional[Dict[str, Any]] = None

class TableBlock(PydanticBase):
    type: Literal["table"]
    headers: List[str]
    rows: List[List[str]]
    data: Optional[Dict[str, Any]] = None

class MatrixBlock(PydanticBase):
    type: Literal["matrix"]
    headers: List[str]
    rows: List[List[str]]
    data: Optional[Dict[str, Any]] = None

class DSGridBlock(PydanticBase):
    type: Literal["ds_grid"]
    row_headers: List[str] = Field(..., description="Labels for each row")
    col_headers: List[str] = Field(..., description="Labels for each column")
    data: Optional[Dict[str, Any]] = None

class GenericBlock(PydanticBase):
    type: Literal["list", "dropdown", "numeric"]
    text: Optional[str] = None
    url: Optional[str] = None
    alt: Optional[str] = None
    headers: Optional[List[str]] = None
    rows: Optional[List[List[str]]] = None
    data: Optional[Dict[str, Any]] = None

# Discriminated union for content blocks
ContentBlock = Annotated[
    Union[
        ParagraphBlock,
        ImageBlock,
        TableBlock,
        MatrixBlock,
        DSGridBlock,
        GenericBlock
    ],
    Field(discriminator="type")
]

# --- Option schema ---
class Option(PydanticBase):
    id: str = Field(..., description="Option label, e.g. 'A'")
    blocks: List[ContentBlock]

# --- Coordinate for DS/Two-Part grid answers ---
class CellCoordinate(PydanticBase):
    row_index: int = Field(..., ge=0)
    column_index: int = Field(..., ge=0)

# --- Answer schema ---
class AnswerSchema(PydanticBase):
    correct_option_id: Optional[str] = None
    selected_choice_index: Optional[int] = None
    selected_pairs: Optional[List[CellCoordinate]] = None
    clicked_hotspot_id: Optional[str] = None

    @field_validator("selected_pairs")
    def validate_pairs(cls, v, info):
        qtype = info.context.get("question_type") if info.context else None
        if qtype == "two-part-analysis" and (not v or len(v) != 2):
            raise ValueError("Must select exactly 2 cells for two-part analysis")
        if qtype == "data-sufficiency" and v and len(v) > 2:
            raise ValueError("At most 2 selections allowed for data-sufficiency")
        return v

# --- Base fields shared by create & read ---
class QuestionBase(PydanticBase):
    type: str = Field(..., description="e.g. 'problem-solving', 'two-part-analysis'")
    content: List[ContentBlock]
    options: List[Option] = Field(default_factory=list)
    answers: AnswerSchema
    tags: List[str] = Field(default_factory=list)
    difficulty: int = Field(1, ge=1, le=7)

class QuestionCreate(QuestionBase):
    parent_id: Optional[UUID] = None
    order: Optional[int] = None

class QuestionRead(QuestionBase):
    kind: Literal["single"] = Field("single", alias="kind")
    id: UUID
    created_at: datetime
    updated_at: datetime

class CompositeQuestionRead(PydanticBase):
    kind: Literal["composite"] = Field("composite", alias="kind")
    group_id: UUID = Field(..., alias="groupId")
    type: str
    passage: List[ContentBlock]
    subquestions: List[QuestionRead]
    total_subquestions: int = Field(..., alias="totalSubquestions")
    next_group_id: Optional[UUID] = Field(None, alias="nextGroupId")

class QuestionSummaryRead(PydanticBase):
    id: UUID
    type: str
    difficulty: int
    tags: List[str]
    parent_id: Optional[UUID] = Field(None, alias="parentId")
    order: Optional[int] = None

QuestionResponse = Union[QuestionRead, CompositeQuestionRead]

class NextQuestionResponse(PydanticBase):
    next_question: Optional[QuestionResponse]
