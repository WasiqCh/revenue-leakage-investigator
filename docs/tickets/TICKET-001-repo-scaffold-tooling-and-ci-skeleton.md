# TICKET-001 - Repo scaffold, tooling and CI skeleton

- **Status:** DONE
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

- [x] `make lint` exits 0 on a clean checkout
- [x] `make test` exits 0 (see deviation 1: an *empty* suite cannot satisfy this)
- [x] ruff reports zero errors
- [x] mypy reports zero errors on `app/`
- [x] eslint reports zero errors

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Deviations and notes

Recorded because they differ from the ticket as written.

1. **`make test` cannot exit 0 on an empty suite.** pytest exits 5 when it
   collects no tests. Instead of an empty `backend/tests/`, this ticket ships
   nine real tests: `test_offline_env.py` guards the offline environment
   (AGENTS.md 1.5) and `test_tooling_contract.py` pins the tooling settings.
2. **`backend/app/__init__.py` was created** even though it is not listed under
   Deliverables. The acceptance criteria require mypy to report zero errors on
   `app/`, and mypy exits 2 with "Cannot read file 'app'" when the package does
   not exist. It is an empty placeholder package; later tickets fill it.
3. **`pytest-env` added to the `dev` extra.** `pyproject.toml` already declared
   `env = ["LLM_MOCK=1", "CUAD_OFFLINE=1"]`, but without this plugin pytest only
   warns "Unknown config option: env" and never sets the variables, so tests
   could reach the network. Verified: removing the plugin fails two tests.
4. **`EXE002` ignored in `[tool.ruff.lint]`.** On Windows, Docker Desktop's bind
   mount reports every file as executable, so ruff flagged every source file.
   File mode is not meaningful here; CI checks out through git.
5. **Frontend additions:** `eslint.config.mjs` (flat config via
   `@eslint/eslintrc`), `.prettierrc`, `.prettierignore`, `package-lock.json`,
   plus `@eslint/eslintrc` and `prettier` as dev dependencies. `npm run lint`
   now calls eslint directly instead of `next lint`, and `format` /
   `format:check` wrap prettier. `frontend/README.md` was reformatted by
   prettier so `format:check` passes.
6. **Makefile split:** `lint` now runs `lint-backend` and `lint-frontend`;
   `fmt` runs `fmt-backend` and `fmt-frontend`. The single `lint` target only
   covered Python, which made "eslint reports zero errors" unverifiable.
7. **Still expected to fail until later tickets:** the `frontend` container
   exits because `npm run dev` has no Next.js app yet (TICKET-041), and the
   `backend` container serves no API because `app.api.main` does not exist yet
   (TICKET-037). Neither affects this ticket's checks.
