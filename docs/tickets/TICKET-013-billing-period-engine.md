# TICKET-013 - Billing period engine

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.5 day
- **Depends on:** TICKET-008

## Goal

Enumerate billing periods with anchor modes, clamping and billable-start resolution.

## What this means

Work out exactly which time window each invoice should cover. This sounds trivial and is not: a deal signed 15 March with 'billing starts the first full period' means March is partly unbilled on purpose - and getting that wrong invents or hides real money.

## Context

Implements anchors (calendar month, anniversary, contract effective day), backward clamping for anchor days 29-31, frequency stepping, stable period_index, and the three commencement overrides (immediate, first full period, next period start). See docs/billing-periods.md.

## Deliverables

- `backend/app/billing/periods.py`
- `backend/tests/unit/test_periods.py`
- `backend/tests/property/test_period_clamping.py`

## Acceptance criteria

- [ ] Hypothesis over anchor days 1-31 across months proves periods are contiguous, non-overlapping and cover the horizon
- [ ] anchor day 31 clamps in February and the next period resumes on the 31st
- [ ] FIRST_FULL_PERIOD produces zero March stub billing in the documented worked example

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
