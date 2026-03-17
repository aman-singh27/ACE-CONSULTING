# JobIntel Backend

Backend API for the JobIntel system — built with **FastAPI**, **PostgreSQL**, **SQLAlchemy (async)**, and **Alembic**.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker & Docker Compose | Latest |

---

## Quick Start

### 1. Install Python dependencies

```bash
cd jobintel/backend
pip install -r requirements.txt
```

### 2. Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and set real values for secrets if deploying beyond local dev.

### 3. Start PostgreSQL

```bash
docker compose up -d
```

Verify the container is running:

```bash
docker ps
# Should show: jobintel_postgres
```

### 4. Run Alembic migrations

```bash
alembic upgrade head
```

### 5. Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

The API is now available at **http://localhost:8000**.

---

## Verification

| Check | How |
|-------|-----|
| Swagger UI | Open http://localhost:8000/docs |
| Health endpoint | `GET http://localhost:8000/api/v1/health` → `{"status":"ok","service":"jobintel-api"}` |
| DB connected | Server logs show *"Database connection successful"* |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py            # FastAPI application entry
│   ├── core/              # Config, logging, security
│   ├── db/                # SQLAlchemy engine, Base, migrations
│   ├── models/            # ORM models (next step)
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic layer
│   ├── api/               # Route definitions & dependencies
│   └── utils/             # Shared helpers
├── alembic/               # Migration scripts
├── alembic.ini
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
