# TICKET-004 - Database engine, session and model conventions

- **Status:** DONE
- **Phase:** 0 - Foundation
- **Effort:** 1.0 day
- **Depends on:** TICKET-002, TICKET-003

## Goal

SQLAlchemy 2.0 engine, session factory, declarative base, custom column types and Alembic wired to the model metadata.

## What this means

The plumbing that lets the app talk to the database, plus special column types so money and date ranges are stored safely rather than as loose numbers.

## Context

Custom types: MoneyType (Decimal), CurrencyCode, HalfOpenDateInterval helpers. Async engine. Alembic autogenerate configured against the shared metadata object.

## Deliverables

- `backend/app/db/engine.py`
- `backend/app/db/session.py`
- `backend/app/db/base.py`
- `backend/app/db/types.py`
- `backend/app/db/enums.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`

All seven exist. `alembic.ini` and `alembic/env.py` are under `backend/` rather
than at the repo root: the Alembic script has to sit beside the `app/` package
it imports, and only `backend/` is mounted into the container. See deviation 1
below.

## Acceptance criteria

- [x] `alembic upgrade head` succeeds on an empty database
      (`make migrate`; also exercised by `tests/integration/test_alembic.py`)
- [x] a test round-trips a Decimal money column with 4 decimal places with no float drift
      (`tests/integration/test_money_type.py`)
- [x] `alembic check` reports no pending model diffs
      (`tests/integration/test_alembic.py`)

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes (46 passed, 1 skipped: the docs-parsing config test,
      which skips because compose only mounts `backend/`, `fixtures/` and `data/`)
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Deviations and decisions (read before continuing)

1. **`alembic.ini` and `env.py` live under `backend/`.** The ticket lists them at
   the repo root, but the Alembic script has to sit beside the `app/` package it
   imports (`prepend_sys_path = .` resolves to `backend/`), and `make migrate`
   already runs `docker compose exec backend alembic upgrade head`. Root-level
   files would be unreachable from inside the container.

2. **No new dependency: the async engine uses psycopg, not asyncpg.** AGENTS.md
   section 2 forbids adding a library that is not on its list. psycopg v3 is on
   the list and speaks both sync and async, so one driver covers the app engine
   and Alembic. `to_psycopg_dsn()` in `engine.py` is the single place that
   normalises a DSN; without it SQLAlchemy silently falls back to psycopg2,
   which is not installed.

3. **The migration DSN is `database_url`, not `database_url_psycopg`.**
   `Settings.database_url_psycopg` deliberately strips the driver so *raw* psycopg
   can parse it; SQLAlchemy needs the opposite. `alembic/env.py` therefore calls
   `to_psycopg_dsn()` itself.

4. **`env.py` renders our custom types as plain SQLAlchemy types.** Autogenerate
   was emitting `app.db.types.MoneyType(...)` into migrations without an import,
   so the migration crashed with `NameError: name 'app' is not defined`. A
   `render_item` hook now emits `sa.Numeric(precision=20, scale=4)`,
   `sa.String(length=3)` and `postgresql.DATERANGE()` instead. This is also the
   safer long-term choice: a migration records the DDL it created rather than
   importing application code that may change later.

5. **`env.py` imports model packages defensively.** `app.models.*` does not exist
   until TICKET-005, so `ModuleNotFoundError` is swallowed. Once those packages
   exist the imports take effect and autogenerate sees the tables.

6. **Two test files beyond the deliverables.** `tests/unit/test_engine.py` covers
   DSN normalisation; `tests/integration/test_alembic.py` runs
   `alembic upgrade head` and `alembic check` so the two shell-level acceptance
   criteria are enforced by `make test` rather than by hand.

7. **`backend/alembic/versions/` is empty on purpose.** TICKET-004 adds no tables,
   so there is nothing to migrate yet; the directory exists with a `.gitkeep` so
   the first real revision (TICKET-005) has somewhere to go. The autogenerate
   path was proved end-to-end with a throwaway model, then reverted - it produced
   `numeric(20, 4)`, `varchar(3)`, `daterange`, `uuid` with
   `gen_random_uuid()` and the `pk_<table>` constraint name.

8. **`TimestampMixin` uses a UUID primary key with a DB-side default**
   (`gen_random_uuid()`), so concurrent workers can insert without coordinating.
   `updated_at` is maintained by `onupdate`, which is SQLAlchemy-side; TICKET-005+
   should add a DB trigger if a raw SQL update needs to bump it too.
