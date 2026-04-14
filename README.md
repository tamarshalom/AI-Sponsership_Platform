# Sponsorship Platform Monorepo

AI-powered sponsorship platform for student clubs and organizations that turns club profiles into sponsor matches, tailored event ideas, outreach emails, and one-click event creation through Luma.

## Inputs
1. Club Profile: name, University/location, mission statement
2. Past Events Hosted: name of event, location on campus, number of attendees, short description
3. Sponsorship Goals: short description, $ amount (optional)

## Outputs
1. List of Sponsors with respective event ideas
2. Email Template to send to sponsors
3. A ready to post Luma Event

---

Full-stack monorepo with:

- `frontend`: Next.js (App Router), TypeScript, Tailwind, shadcn/ui baseline
- `backend`: FastAPI + SQLAlchemy + Alembic
- `db`: PostgreSQL with `pgvector` enabled

## Project Structure

```text
.
├── frontend/
├── backend/
├── shared/
└── docker-compose.yml
```

## Prerequisites

- Docker + Docker Compose
- (Optional local dev) Node.js 20+, Python 3.12+

## Quick Start (Docker)

1. Start everything:

```bash
docker compose up --build
```

2. Open:
   - Frontend (Docker maps host **3002** → container 3000): [http://localhost:3002](http://localhost:3002)
   - Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs) (also [http://localhost:8000/](http://localhost:8000/) redirects here)
   - Backend health: [http://localhost:8000/health](http://localhost:8000/health)

Alembic migrations run automatically on backend startup and create the `vector` extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Local Dev Without Docker

### Database

Run PostgreSQL with pgvector (example with Docker only for DB):

```bash
docker run --name sponsorship-db \
  -e POSTGRES_USER=sponsorship \
  -e POSTGRES_PASSWORD=sponsorship \
  -e POSTGRES_DB=sponsorship \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

## Frontend -> Backend Connectivity

Two layers are configured:

- **Next.js rewrite proxy** in `frontend/next.config.mjs`:
  - `/api/backend/*` -> `BACKEND_INTERNAL_URL/*`
- **FastAPI CORS** in `backend/app/main.py`:
  - allows `FRONTEND_ORIGINS` (comma-separated; default includes `http://localhost:3000`, `3001`, and `3002`)

This means browser calls can use:

```text
/api/backend/health
```

## Alembic Notes

- Config: `backend/alembic.ini`
- Env: `backend/alembic/env.py`
- Initial migration: `backend/alembic/versions/20260407_0001_init.py`
- IVFFlat index on sponsor embeddings (cosine): `backend/alembic/versions/20260407_0002_ivfflat_sponsors_embedding.py`

Backend services (for reuse and tests): `backend/app/services/embedding_service.py` (OpenAI embeddings) and `backend/app/services/sponsor_match_service.py` (pgvector `<=>` matching).

To create another migration:

```bash
cd backend
alembic revision -m "describe change"
alembic upgrade head
```
