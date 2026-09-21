# ADR-002: PostgreSQL 16 + pgvector, and Docker is the only supported way to run it

**Status:** Accepted — 2026-09-21

## What this means

Everything is stored in one database, **PostgreSQL 16**, with an add-on called **pgvector** that stores and searches **embeddings** — lists of numbers representing the meaning of a piece of text, so we can find relevant contract clauses even when the words differ. There is no second database and no lighter alternative. **Docker** packages an application and its dependencies into a container so it runs identically anywhere; **Docker Compose** starts the database, API, worker and website with one command. Docker is the only supported path: no SQLite mode, no in-memory database, no shortcut that skips the database. The practical consequence is that Wasiq, who has no Docker, cannot run the application locally. Umer, who has Docker, runs it, and Wasiq reviews through the deployed instance and the recorded demo.

## Context

Three forces pushed us here. Contract clauses must be retrieved by meaning, not keyword, and retrieval is a headline capability rather than a supporting detail — pgvector puts it inside the database we already need. The guardrail in [ADR-004](ADR-004-read-only-role-guardrail.md) depends on real database roles, and SQLite has no grants, so "the AI cannot change an invoice" would degrade from a permission into a promise. And `FOR UPDATE SKIP LOCKED` in [ADR-005](ADR-005-postgres-job-queue-not-celery.md) is Postgres-specific. The cost is real and we name it rather than hide it: a teammate without Docker cannot run the app.

## Decision

**PostgreSQL 16 with the pgvector extension, run via Docker Compose. Docker is the only supported execution path — no SQLite, no in-memory fallback, no "lite mode".**

- `docker-compose.yml` defines `db`, `api`, `worker` and `web`.
- The database image is pinned and the pgvector extension is enabled by migration.
- `.env.example` holds connection settings; there is no alternative DSN scheme.
- Tests run against the real Postgres container and never fall back to another engine.
- Onboarding documentation states plainly that Docker is a prerequisite.

## Alternatives considered

- **SQLite locally, Postgres in production.** Rejected. Two engines mean two behaviours: roles, `SKIP LOCKED` and much of the date arithmetic in [ADR-006](ADR-006-act-act-proration-half-open-intervals.md) differ, so local tests would prove things about a system we do not ship.
- **An in-memory database for tests.** Rejected for the same reason, and it cannot store vectors, so retrieval tests — the most likely thing to break — would have to be skipped.
- **A hosted Postgres by default.** Rejected for the default path: credentials, cost, latency and a network dependency in `make test`, plus a demo that is fragile on conference wifi. It remains a valid deployment target.
- **DuckDB or a file-based analytical store.** Rejected. Excellent for analysis, but no roles, no row locking, and no matching vector index story.

## Consequences

**Easier.** One datastore to run, migrate, seed and back up. Real vector search with no extra service. The read-only role is a genuine database grant. Concurrency is testable because `SKIP LOCKED` exists. Local development closely matches production, so "it works on my machine" is largely eliminated.

**Harder.** Nobody can start the app without Docker Desktop installed and running. Docker on Windows costs memory and needs a working WSL2 backend. Container start-up adds tens of seconds to the first run of each session, so the edit-test loop is slower than a bare Python process would be.

**Negative.** Wasiq, who defines the acceptance criteria, cannot reproduce a failure locally and must describe bugs rather than show a stack trace. We mitigate with a recorded demo, a deployed environment and screenshots in review, but it is a genuine loss of autonomy and a known cost of this decision.

## How to reverse it

Supporting a non-Docker path means adding an alternative engine or a hosted database and proving that roles, `SKIP LOCKED` and proration behave identically there. That is a portability project, not a config change, and it weakens the enforcement story in ADR-004 while it is in progress.
