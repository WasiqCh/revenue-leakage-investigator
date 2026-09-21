# TICKET-042 - Case queue UI

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 1.5 day
- **Depends on:** TICKET-041, TICKET-038

## Goal

The main working screen: a filterable table of investigation cases.

## What this means

The screen Finance lives in. Filters that stick in the URL, clear badges for severity and confidence, and one row per ongoing problem rather than one per month.

## Context

Filters map directly to API parameters and persist in the URL. Empty, loading and error states are all designed.

## Deliverables

- `frontend/app/cases/page.tsx`
- `frontend/components/case-table.tsx`

## Acceptance criteria

- [ ] filters map to API params and are URL-persisted
- [ ] a 5-period case renders as one row showing the range
- [ ] empty, loading and error states are covered

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
