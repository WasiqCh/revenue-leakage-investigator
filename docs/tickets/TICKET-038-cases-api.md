# TICKET-038 - Cases API

- **Status:** TODO
- **Phase:** 7 - API
- **Effort:** 1.5 day
- **Depends on:** TICKET-037, TICKET-022

## Goal

List and detail endpoints for investigation cases plus the change timeline.

## What this means

Let the website read cases: filter by status, customer, confidence band and date, and fetch the full detail including evidence and the change history.

## Context

Filters compose. Detail returns the case, its periods, evidence, report, recommendation and agent trace.

## Deliverables

- `backend/app/api/routers/cases.py`
- `backend/tests/integration/test_cases_api.py`

## Acceptance criteria

- [ ] filters compose correctly and are covered by tests
- [ ] detail returns the full evidence chain with resolvable citations
- [ ] list is paginated with a stable sort
- [ ] a case with 5 affected periods returns one row with the correct range

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
