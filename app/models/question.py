from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class Exam(str, Enum):
    GRE = "GRE"
    GMAT = "GMAT"

class QuestionType(str, Enum):
    RC = "Reading Comprehension"
    CR = "Critical Reasoning"
    QUANT = "Quantitative"

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class Option(BaseModel):
    id: str
    text: str

class Question(BaseModel):
    id: int
    exam: Exam
    type: QuestionType
    tags: List[str] = []
    difficulty: DifficultyLevel

    prompt: str
    options: List[Option]
    correct_option: Optional[str]
    explanation: Optional[str]
