# TICKET-002 - Docker Compose stack

- **Status:** TODO
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

- [ ] `docker compose up -d` reaches all-healthy
- [ ] `psql -c "select extname from pg_extension"` includes `vector`
- [ ] backend `/healthz` returns 200
- [ ] frontend serves on port 3000

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
