# TICKET-024 - Leakage maths and FX normalisation

- **Status:** TODO
- **Phase:** 4 - Cases and money
- **Effort:** 1.5 day
- **Depends on:** TICKET-023, TICKET-008

## Goal

Compute expected, actual, potential, historical, confirmed and annualised leakage.

## What this means

The money layer. Crucially it separates 'might be lost' from 'we are confident' from 'we actually got it back' - three different numbers that must never be conflated in a report to Finance.

## Context

Recurring cases annualise as latest_delta x 12 / frequency_months; one-off cases annualise to themselves. FX uses the rate as of the relevant date, walking back to the nearest prior business day. See docs/evaluation.md.

## Deliverables

- `backend/app/cases/leakage.py`
- `backend/app/money/fx.py`
- `backend/tests/unit/test_leakage.py`
- `backend/tests/property/test_money_conservation.py`

## Acceptance criteria

- [ ] confirmed never exceeds historical (property test)
- [ ] a 5-period recurring case annualises to latest_delta x 12
- [ ] a one-off case annualises to itself
- [ ] a period with no usable FX rate is flagged insufficient_data and excluded from totals

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
