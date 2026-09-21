# TICKET-004 - Database engine, session and model conventions

- **Status:** TODO
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
- `alembic.ini`
- `alembic/env.py`

## Acceptance criteria

- [ ] `alembic upgrade head` succeeds on an empty database
- [ ] a test round-trips a Decimal money column with 4 decimal places with no float drift
- [ ] `alembic check` reports no pending model diffs

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
