# TICKET-002 - Docker Compose stack

- **Status:** DONE
- **Phase:** 0 - Foundation
- **Effort:** 0.5 day
- **Depends on:** TICKET-001

## Goal

Bring up Postgres 16 + pgvector, backend, worker and frontend with healthchecks.

## What this means

One command starts the whole app. Docker is the only supported way to run this project - there is deliberately no lightweight fallback, so every developer runs the same environment.

## Context

Four services: db (pgvector/pgvector:pg16), backend, worker, frontend. Named volumes persist data. Healthchecks gate startup order. `scripts/init_db.sql` enables the vector, pg_trgm and pgcrypto extensions.

## Deliverables

- `docker-compose.yml`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `scripts/init_db.sql`

## Acceptance criteria

- [x] `docker compose up -d` reaches all-healthy
- [x] `psql -c "select extname from pg_extension"` includes `vector`
- [x] backend `/healthz` returns 200
- [x] frontend serves on port 3000

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Deviations and notes

Recorded because they differ from the ticket as written.

1. **Three placeholder modules were created** that later tickets own. The
   compose entrypoints reference `app.api.main` (TICKET-037),
   `app.jobs.worker` (TICKET-032) and a Next.js app (TICKET-041). Without
   something at those paths the backend serves nothing, the worker exits with
   `ModuleNotFoundError`, and the frontend container exits — so three of the
   four acceptance criteria were unreachable. Each placeholder is deliberately
   minimal and is replaced by its owning ticket:
   - `backend/app/api/main.py` — FastAPI app exposing only `GET /healthz`.
   - `backend/app/jobs/worker.py` — idles until SIGTERM.
   - `frontend/app/{layout,page}.tsx` plus `frontend/tsconfig.json` — one page.
2. **Healthchecks use Python and Node, not curl.** Neither `python:3.13-slim`
   nor `node:22-slim` ships curl. The backend probe uses `urllib`, the website
   probe uses Node's built-in `fetch`.
3. **The worker healthcheck must strip the SQLAlchemy driver prefix.**
   `DATABASE_URL` is `postgresql+psycopg://...`, which plain psycopg cannot
   parse; the check rewrites it to `postgresql://` before connecting.
4. **Dockerfile changes.** The backend now copies `app/` before
   `pip install -e ".[dev]"` so the editable install registers the package, and
   the `|| pip install fastapi uvicorn` fallback was removed — it could hide a
   failed install and leave ruff, mypy and pytest missing. The frontend now
   uses `npm ci` with the committed lockfile instead of `npm install`.
5. **`frontend/next-env.d.ts` added to `.gitignore`.** `next dev` regenerates
   it on every run.
6. **`backend/tests/test_database_stack.py` is extra** (not a named
   deliverable). It asserts the three extensions are installed and that
   `rl_readonly` cannot create a table, which automates the second acceptance
   criterion and backs ADR-004. It skips when `DATABASE_URL` is unset.
7. **ADR-002 names the services `db`, `api`, `worker`, `web`;** the compose
   file uses `db`, `backend`, `worker`, `frontend`. Left as-is — the Makefile
   and later tickets refer to the current names — and noted here rather than
   silently rewritten.
