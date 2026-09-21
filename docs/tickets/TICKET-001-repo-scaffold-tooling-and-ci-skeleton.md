# TICKET-001 - Repo scaffold, tooling and CI skeleton

- **Status:** TODO
- **Phase:** 0 - Foundation
- **Effort:** 0.5 day
- **Depends on:** none

## Goal

Establish the monorepo layout, linting, formatting, type checking and test configuration.

## What this means

Set up the workshop before building anything: folder layout, code style rules, and an automated check that runs on every change so bad code is caught immediately.

## Context

ruff + mypy (strict on app/) for Python, eslint + prettier for TypeScript, pytest for tests. CI runs lint and unit tests without needing network access or any service beyond Postgres.

## Deliverables

- `backend/pyproject.toml`
- `frontend/package.json`
- `.github/workflows/ci.yml`
- `.gitignore`
- `Makefile`
- `backend/tests/`
- `frontend/`

## Acceptance criteria

- [ ] `make lint` exits 0 on a clean checkout
- [ ] `make test` exits 0 on an empty test suite
- [ ] ruff reports zero errors
- [ ] mypy reports zero errors on `app/`
- [ ] eslint reports zero errors

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
