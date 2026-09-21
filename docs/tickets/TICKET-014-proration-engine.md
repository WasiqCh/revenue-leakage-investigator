# TICKET-014 - Proration engine

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.0 day
- **Depends on:** TICKET-013

## Goal

Compute partial-period amounts using ACT/ACT day counts and mid-period splitting.

## What this means

If a customer is billed for half a month, charge exactly half. Uses real calendar days, and splits a period into pieces when the quantity changes partway through.

## Context

factor = billed_days / period_days, quantised to 2 decimal places with ROUND_HALF_UP. Mid-period quantity changes split at each change date; each piece is prorated and summed.

## Deliverables

- `backend/app/billing/proration.py`
- `backend/tests/unit/test_proration.py`
- `backend/tests/property/test_proration.py`

## Acceptance criteria

- [ ] the worked example yields $6,000 expected for 15 of 30 days
- [ ] splitting a period at a change date and summing equals prorating the whole period when quantity is constant
- [ ] no float appears anywhere in the module

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
