# Clara

AI-powered test prep backend for exams like GMAT and GRE, built with FastAPI.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Database Setup](#database-setup)
  - [Running Migrations](#running-migrations)
- [Running the App](#running-the-app)
- [API Reference](#api-reference)
  - [Health Check](#health-check)
  - [Users](#users)
  - [Questions](#questions)
  - [Chat](#chat)
  - [Dashboard](#dashboard)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- CRUD operations for questions and user accounts
- Chat interface powered by OpenAI embeddings and pgvector
- Dashboard analytics endpoints
- Health check endpoint for monitoring
- Modular router structure for easy extension

## Tech Stack

- **FastAPI** — Web framework with automatic OpenAPI docs
- **SQLAlchemy** — ORM for Postgres
- **Pydantic** — Data validation and settings management
- **psycopg2-binary** — Postgres driver
- **pgvector** — Vector extension for semantic search
- **Uvicorn** — ASGI server

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- [Git](https://git-scm.com/)

### Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/kanishkkatara/clara.git
   cd clara
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

```dotenv
DATABASE_URL=postgresql://user:password@localhost:5432/clara_db
OPENAI_API_KEY=your_openai_api_key
# Optional
PGVECTOR_DATABASE_URL=postgresql://user:password@localhost:5432/clara_db
``` 

### Database Setup

1. Ensure Postgres is running and the target database exists.
2. (Optional) Enable the pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### Running Migrations

(Coming soon) We recommend integrating Alembic for versioned migrations.

## Running the App

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

## API Reference

### Health Check

- **GET** `/health`
  - Response: `{ "status": "ok" }`

### Users

- **POST** `/users/` — Create a new user
- **GET** `/users/{user_id}` — Retrieve user details

### Questions

- **POST** `/questions/` — Add a new question
- **GET** `/questions/{question_id}` — Fetch question details
- **PUT** `/questions/{question_id}` — Update a question
- **DELETE** `/questions/{question_id}` — Remove a question

### Chat

- **POST** `/chat/` — Send a message and receive AI response

### Dashboard

- **GET** `/dashboard/analytics` — Retrieve usage and performance metrics

## Usage Examples

Create a question via cURL:
```bash
curl -X POST http://localhost:8000/questions/ \
  -H "Content-Type: application/json" \
  -d '{
    "type": "problem-solving",
    "content": [{ "text": "What is 2+2?" }],
    "options": ["3","4","5","6"],
    "answer": 1
  }'
```

## Contributing

1. Fork the repo
2. Create a feature branch
3. Open a pull request

Please follow code style, add tests, and update documentation.

## License

MIT © Kanishk Katara
