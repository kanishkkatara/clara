from app.models.user import User

def get_user_by_id(user_id: int) -> User:
    return User(
        id=user_id,
        name="John Doe",
        email="john.doe@gmail.com",
        password="hashed_password",
        role="Student",
        exams=["GRE", "SAT"],
        created_at="2023-10-01T12:00:00Z",
        updated_at="2023-10-01T12:00:00Z",
        is_active=True,
    )