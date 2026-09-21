# TICKET-037 - FastAPI skeleton, seeded roles and error model

- **Status:** TODO
- **Phase:** 7 - API
- **Effort:** 1.0 day
- **Depends on:** TICKET-006

## Goal

Application factory, OpenAPI, uniform error responses, pagination and seeded roles.

## What this means

Stand up the web API with predictable error messages and three pretend user types (viewer, analyst, approver). This is explicitly not real login - it exists so the demo can show that only an approver can approve.

## Context

A seeded-role dependency driven by a header. Explicitly out of scope: real authentication, multi-tenancy.

## Deliverables

- `backend/app/api/main.py`
- `backend/app/api/deps.py`
- `backend/app/api/errors.py`
- `backend/tests/integration/test_api_skeleton.py`

## Acceptance criteria

- [ ] /openapi.json validates
- [ ] every error response matches the documented envelope
- [ ] an approve endpoint called as viewer returns 403
- [ ] unknown roles are rejected

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
