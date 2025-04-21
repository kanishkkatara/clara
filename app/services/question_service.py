from app.models.question import DifficultyLevel, Exam, Question, Option, QuestionType
from typing import List

def get_questions(tags: List[str] = None) -> List[Question]:
    if tags is None:
        tags = []
    return [
        Question(
            id=1,
            exam=Exam.GRE,
            type=QuestionType.RC,
            tags=tags,
            difficulty=DifficultyLevel.EASY,
            prompt="What is the capital of France?",
            options=[
                Option(id="A", text="Paris"),
                Option(id="B", text="London"),
                Option(id="C", text="Berlin"),
                Option(id="D", text="Madrid"),
            ],
            correct_option="A",
            explanation="Paris is the capital of France.",
        ),
        Question(
            id=2,
            exam=Exam.GRE,
            type=QuestionType.RC,
            tags=tags,
            difficulty=DifficultyLevel.MEDIUM,
            prompt="What is the capital of Germany?",
            options=[
                Option(id="A", text="Berlin"),
                Option(id="B", text="London"),
                Option(id="C", text="Paris"),
                Option(id="D", text="Madrid"),
            ],
            correct_option="A",
            explanation="Berlin is the capital of Germany.",
        ),
    ]

def get_question_by_id(question_id: int) -> Question:
    return Question(
        id=question_id,
        exam=Exam.GRE,
        type=QuestionType.RC,
        tags=["tag1", "tag2"],
        difficulty=DifficultyLevel.EASY,
        prompt="What is the capital of France?",
        options=[
            Option(id="A", text="Paris"),
            Option(id="B", text="London"),
            Option(id="C", text="Berlin"),
            Option(id="D", text="Madrid"),
        ],
        correct_option="A",
        explanation="Paris is the capital of France.",
    )
