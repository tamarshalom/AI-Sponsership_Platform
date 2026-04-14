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

### Ingest broader sponsor datasets (recommended)

Use this for partner exports / spreadsheets instead of only relying on the demo seed list.

```bash
docker compose exec backend python scripts/ingest_sponsors_csv.py /app/path/to/sponsors.csv --source "partner-export"
```

Expected CSV columns (minimum):
- `name`, `mission`

Common optional columns:
- `description`, `industries`, `support_types`, `website_url`, `locations`
- `budget_min_cents`, `budget_max_cents`, `contact_name`, `contact_email`, `external_id`
- any `meta_*` columns are stored in sponsor metadata.

Notes:
- `industries` / `support_types` / `locations` accept comma, `;`, or `|` separators.
- Existing sponsors are deduped by website domain first, then by case-insensitive name.

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

- **Web UI URL:** [http://localhost:3000](http://localhost:3000) — this is the Next.js app (`/` and `/wizard`).  
- **API only:** [http://localhost:8000](http://localhost:8000) serves FastAPI (e.g. `/docs`), not the React pages.

Use **`npm ci`** (not `npm install`) when you want the same dependency tree as everyone else (`package-lock.json`).

### Frontend shows 404 on `/` (dev only)

1. **Wrong port** — With Docker Compose, the UI is mapped to **[http://localhost:3002](http://localhost:3002)** (see `docker-compose.yml`), not `3000`. With `npm run dev`, use **`http://localhost:3000`**.
2. **File watcher limits (macOS)** — If the terminal shows `EMFILE: too many open files` or `Watchpack Error`, Next may never compile `app/` routes and every path returns 404. Try:
   - `npm run dev:poll` (polling mode, easier on watchers), or  
   - Raise the limit: `ulimit -n 10240` in the same terminal before `npm run dev`, or  
   - One-off check: `npm run build && npm run start` — if that works, the app is fine and the issue is dev watching.

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
