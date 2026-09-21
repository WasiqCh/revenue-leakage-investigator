# TICKET-018 - Detectors batch 1

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 2.0 days
- **Depends on:** TICKET-016

## Goal

Implement seat underbilling, renewal price not applied, amendment not propagated, and premium feature not billed.

## What this means

The four most common ways companies lose money: fewer seats billed than sold, an old price still in use after a renewal, a signed amendment never reaching billing, and a paid feature switched on but never charged for.

## Context

Each detector is a pure function over the canonical model that emits a reconciliation_result when its condition holds.

## Deliverables

- `backend/app/detect/checks/seat_underbilling.py`
- `backend/app/detect/checks/renewal_price.py`
- `backend/app/detect/checks/amendment_propagation.py`
- `backend/app/detect/checks/premium_feature.py`
- `backend/tests/integration/test_checks_batch1.py`

## Acceptance criteria

- [ ] each detector fires exactly on its generated scenario
- [ ] each produces zero false positives across 100 clean generated customers
- [ ] each has a Hypothesis test for boundary quantities and prices

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
