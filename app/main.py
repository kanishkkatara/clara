from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import engine, Base
import app.api.questions as questions
import app.api.users as users
import app.api.onboarding as onboarding

app = FastAPI(title="Clara API (with Postgres)")

# CORS
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# include routers
app.include_router(questions.router, prefix="/api/questions")
app.include_router(users.router, prefix="/api/users")
app.include_router(onboarding.router, prefix="/api/onboarding")

# create tables
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to Clara!"}
