from fastapi import FastAPI
from app.api import questions, users, onboarding

app = FastAPI(title="Clara API (Mock)")

app.include_router(questions.router, prefix="/api/questions")
app.include_router(users.router, prefix="/api/users")
app.include_router(onboarding.router, prefix="/api/onboarding")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Clara!"}