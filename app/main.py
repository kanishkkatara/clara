from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dashboard, health, questions, settings, users, chat

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://open-prep-fe.vercel.app"
]

app = FastAPI(title="Clara API (with Postgres)")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api/health")
app.include_router(questions.router, prefix="/api/questions")
app.include_router(users.router, prefix="/api/users")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(dashboard.router, prefix="/api/dashboard")
app.include_router(settings.router, prefix="/api/settings")

@app.get("/")
async def read_root():
    return {"message": "Welcome to Clara!"}
