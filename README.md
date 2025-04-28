# Clara

Clara is an AI-powered test prep platform for exams like GMAT.

## Setup Instructions

### 1. Clone the repository

```bash
git clone git@github.com:kanishkkatara/clara.git
cd clara
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```
### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

Server will start at: http://127.0.0.1:8000