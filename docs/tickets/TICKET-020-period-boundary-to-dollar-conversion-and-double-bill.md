# TICKET-020 - Period-boundary to dollar conversion and double-billing

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.0 day
- **Depends on:** TICKET-014, TICKET-016

## Goal

Turn date mismatches into money, and detect the same period being billed twice.

## What this means

A one-month gap between contract start and billing start is not a vague problem - it is a specific number of days times a daily rate. Also catches the opposite error: over-billing, which must be reported separately and never quietly netted off.

## Context

Uses interval algebra and daily_rate = period_amount / period_days. Over-billing yields a negative delta surfaced as its own finding.

## Deliverables

- `backend/app/detect/checks/period_boundary.py`
- `backend/tests/unit/test_period_boundary.py`

## Acceptance criteria

- [ ] the documented worked example returns $6,000
- [ ] a leading-gap case returns the correct positive amount
- [ ] a billed-early case returns a negative (over-billing) delta
- [ ] a synthetic duplicate-coverage case is detected with the correct summed amount

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
