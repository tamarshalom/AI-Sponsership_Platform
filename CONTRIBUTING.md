# Contributing

This repo is set up so everyone runs the **same code** and **same dependency versions**. Use **GitHub** for code (not file sharing over chat), and keep **secrets out of git**.

## Before you write code

1. **Clone** the repo and use the branch your team agreed on (often `main` or a feature branch).
2. **Pull** before you start: `git pull`.
3. **Create a branch** for your work: `git checkout -b yourname/short-description`.
4. Open a **Pull Request** when ready; get a quick review before merging.

## Secrets (required for AI + matching)

Never commit API keys or `.env` files.

1. Copy the examples:

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

2. Edit **`backend/.env`** and set:

   - `OPENAI_API_KEY` — get your own key from [OpenAI API keys](https://platform.openai.com/api-keys) (recommended).  
   - Do **not** paste keys into Discord/slack long-term; use a password manager or each person uses their own key.

3. Restart the backend after changing `.env`.

## Run everything (recommended: Docker)

From the **repository root** (where `docker-compose.yml` is):

```bash
docker compose up --build
```

- **API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- **Health:** [http://localhost:8000/health](http://localhost:8000/health)  
- **Web UI:** [http://localhost:3002](http://localhost:3002) (if port `3002` is in `docker-compose.yml`; change if it conflicts on your machine)

After the stack is up, **seed sponsors** (needed for sponsor matching):

```bash
docker compose exec backend python scripts/seed_sponsors.py
```

Requires a valid `OPENAI_API_KEY` in `backend/.env` (embeddings API call).

## Run without Docker (advanced)

You need **PostgreSQL with pgvector**, Python 3.12+, and Node 20+.

**Database:** run only Postgres (see root `README.md`) or use the `pgvector/pgvector` image.

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # then add OPENAI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Use **`npm ci`** (not `npm install`) when you want the same dependency tree as everyone else (`package-lock.json`).

## Dependency “source of truth”

| Stack   | Lock file / manifest        |
|---------|-----------------------------|
| Python  | `backend/requirements.txt`  |
| Node    | `frontend/package-lock.json` |

When you add a Python or Node dependency, commit the updated lockfile/requirements so teammates stay in sync.

## Troubleshooting: “Internal Server Error” (500)

The UI often only shows **500**. Check the **real** error in:

- **Terminal** where `uvicorn` or `docker compose` is running, or  
- **Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs) — run the same endpoint and read the response body.

Common causes:

| Symptom / cause | What to do |
|-----------------|------------|
| **`OPENAI_API_KEY` missing or wrong** | Set it in `backend/.env`, name must be exactly `OPENAI_API_KEY`. Restart backend. |
| **Using Docker but no `.env`** | Create `backend/.env` from `.env.example` *before* `docker compose up` (Compose loads this file for the backend service). |
| **Database not running / wrong URL** | With Docker, use the default `DATABASE_URL` in `.env.example` pointing at `db:5432`. Running backend **on the host** while Postgres is **only in Docker** usually means `DATABASE_URL` should use `localhost:5432` and Postgres must publish port `5432`. |
| **Migrations not applied** | `docker compose exec backend alembic upgrade head` or let the backend container run migrations on startup. |
| **Empty sponsor matches** | Run the seed script (see above). Matching needs rows with **non-null** `embedding` in `sponsors`. |
| **Port already in use** | Change the host port in `docker-compose.yml` (e.g. frontend `3002:3000`) or stop the other app using that port. |
| **Wrong Git branch** | `git checkout tamars-branch` (or your team branch) and `git pull`. |

## Pull request checklist

- [ ] Branch is up to date with the target branch (`git pull origin …`).
- [ ] `backend/.env` and `frontend/.env.local` are **not** committed.
- [ ] If you changed dependencies, `requirements.txt` / `package-lock.json` are updated and committed.
- [ ] Short PR description: what changed and how to test.

## Questions?

Open a **GitHub Issue** on the repo so the whole team sees the answer.
