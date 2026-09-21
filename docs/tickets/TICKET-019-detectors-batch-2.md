# TICKET-019 - Detectors batch 2

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 2.5 days
- **Depends on:** TICKET-016, TICKET-017

## Goal

Implement expired discount, services not invoiced, start-date mismatch, usage over-entitlement, SKU rename and duplicate-customer split.

## What this means

Six more patterns, including the ones that catch honest mistakes (a discount that expired but is still being applied) and data chaos (one customer split across two records, so part of their subscription vanishes).

## Context

Same shape as batch 1. The expired-discount detector must consult the exception registry so a grandfathered discount is not reported as leakage.

## Deliverables

- `backend/app/detect/checks/discount_expiry.py`
- `backend/app/detect/checks/services.py`
- `backend/app/detect/checks/start_date.py`
- `backend/app/detect/checks/usage_entitlement.py`
- `backend/app/detect/checks/sku_rename.py`
- `backend/app/detect/checks/duplicate_split.py`
- `backend/tests/integration/test_checks_batch2.py`

## Acceptance criteria

- [ ] each detector fires exactly on its generated scenario and no others
- [ ] DISCOUNT_EXPIRED_STILL_APPLIED does NOT fire when an approved_exception grandfathers the discount (asserted explicitly)
- [ ] zero false positives across 100 clean generated customers

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
