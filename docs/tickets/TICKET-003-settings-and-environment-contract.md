# TICKET-003 - Settings and environment contract

- **Status:** TODO
- **Phase:** 0 - Foundation
- **Effort:** 0.5 day
- **Depends on:** TICKET-001

## Goal

Typed settings object covering every configurable value in the system.

## What this means

All the knobs in one place, with clear names. If something important is missing, the app refuses to start rather than silently guessing.

## Context

Pydantic v2 `Settings`. Covers database URL, LLM base URL / key / model, reporting currency, money tolerances, confidence weights, agent budgets, and the CUAD source / cache / offline flags.

## Deliverables

- `backend/app/config.py`
- `.env.example`
- `backend/tests/unit/test_config.py`

## Acceptance criteria

- [ ] missing DATABASE_URL raises a validation error naming the field
- [ ] every setting is documented in .env.example
- [ ] a test asserts defaults for tolerances and confidence weights match the documented constants
- [ ] no code reads os.environ directly outside config.py

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
