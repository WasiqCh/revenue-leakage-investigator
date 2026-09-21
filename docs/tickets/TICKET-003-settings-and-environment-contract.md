# TICKET-003 - Settings and environment contract

- **Status:** DONE
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

- [x] missing DATABASE_URL raises a validation error naming the field
- [x] every setting is documented in .env.example
- [x] a test asserts defaults for tolerances and confidence weights match the documented constants
- [x] no code reads os.environ directly outside config.py

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Deviations and decisions

Decisions taken by the repo owner while implementing:

1. **Tolerance names follow the docs.** `MONEY_TOLERANCE_ABS` and
   `MONEY_TOLERANCE_PCT` (the names used in `docs/billing-periods.md`) are the
   only spellings. `.env.example` was updated to match; no backwards aliases
   were added because nothing else in the codebase used the older
   `..._ABSOLUTE` / `..._RELATIVE` spellings yet.

2. **Agent budgets did not exist anywhere.** The TRD lists "agent budgets" among
   the critical values and requires a `budget_exhausted` terminal state, but no
   numbers were documented. This ticket defines them:
   `AGENT_MAX_STEPS=12`, `AGENT_MAX_TOOL_CALLS=24`, `AGENT_TOKEN_BUDGET=20000`,
   `AGENT_TIMEOUT_SECONDS=120`, `AGENT_MAX_RETRIES=2`.

3. **Settings come from the process environment only** (the "Docker path").
   `docker-compose.yml` injects them; no `.env` file is read at runtime. A
   missing required value is therefore always a loud start-up failure rather
   than a silent fallback.

4. **Embeddings endpoint added.** `EMBEDDING_URL` is explicit when set, and is
   otherwise derived from `LLM_BASE_URL` (the gateway in use serves chat at
   `/v1` and embeddings at `/api/v1/embeddings`). `EMBEDDING_DIMENSIONS` is
   asserted `<= 2000` because pgvector cannot index wider vectors. Carried
   forward for TICKET-027 (provider adapter): the `openrouter/` model-id prefix
   and retry with backoff.

5. **The `os.environ` rule is enforced over `backend/app` only.** A test greps
   every module under `app/` except `config.py`. The two TICKET-001 tests still
   read `os.environ` because their job is to assert the variables `pytest-env`
   sets — that is test code asserting the environment, not application code
   reading configuration.

6. **`make verify` is not runnable yet.** It runs `alembic upgrade/downgrade`,
   and no migration exists until TICKET-005. Verification for this ticket was
   `ruff check`, `ruff format --check`, `mypy app` (6 files clean), `pytest`
   (28 passed, 1 skipped — `docs/` is not mounted in the backend container, so
   the docs-parsing test skips there; it passes when run from a full checkout),
   plus frontend `eslint` and `prettier --check`.
