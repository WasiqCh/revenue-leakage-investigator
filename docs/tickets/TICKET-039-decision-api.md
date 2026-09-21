# TICKET-039 - Decision API

- **Status:** TODO
- **Phase:** 7 - API
- **Effort:** 1.0 day
- **Depends on:** TICKET-038, TICKET-023

## Goal

Approve and reject endpoints that record outcomes and drive the state machine.

## What this means

Where a human says yes or no. Approving is deliberately idempotent - clicking twice must not double-count recovered money.

## Context

Only operable on CONFIRMED_FOR_REVIEW or NEEDS_REVIEW cases. Records case_outcome and writes an audit event.

## Deliverables

- `backend/app/api/routers/decisions.py`
- `backend/tests/integration/test_decisions_api.py`

## Acceptance criteria

- [ ] approving an already-approved case is a no-op and returns 200
- [ ] rejecting requires a reason code
- [ ] a viewer cannot approve
- [ ] approving writes one audit_event and one case_outcome
- [ ] the recovered amount appears in the ledger query

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
