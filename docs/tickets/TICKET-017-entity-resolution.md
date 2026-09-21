# TICKET-017 - Entity resolution

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.0 day
- **Depends on:** TICKET-005

## Goal

Match the same customer or product across systems that name it differently.

## What this means

'Acme Corp' in the CRM, 'ACME Corporation Ltd' in billing and 'Acme Corporation' on the contract are one customer. Until we prove that, every comparison is meaningless.

## Context

Exact id, exact name, domain and fuzzy name matching. Writes entity_resolution_match with a confidence; auto-accepts above the high threshold, flags needs_review in the middle band so a human can confirm.

## Deliverables

- `backend/app/detect/entity_resolution.py`
- `backend/tests/unit/test_entity_resolution.py`

## Acceptance criteria

- [ ] exact ids always auto-accept
- [ ] a DUPLICATE_CUSTOMER_SPLIT scenario yields one needs_review match
- [ ] false-match rate on generated clean pairs is zero

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
