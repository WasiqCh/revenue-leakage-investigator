# TICKET-016 - Detector framework and idempotent persistence

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.0 day
- **Depends on:** TICKET-015, TICKET-006

## Goal

A registry of checks that write reconciliation results without ever duplicating them.

## What this means

The reusable machinery every comparison plugs into. Running it twice must never create duplicate findings - otherwise the case queue fills with repeats and nobody trusts it.

## Context

Registry maps check_code to a callable. Results are keyed for idempotency. Tolerances come from config, and each run is stamped with a config hash so a changed configuration is traceable.

## Deliverables

- `backend/app/detect/framework.py`
- `backend/app/detect/checks/registry.py`
- `backend/tests/integration/test_reconciliation_idempotency.py`

## Acceptance criteria

- [ ] running reconciliation twice on the same data creates zero duplicate rows
- [ ] tolerance boundary behaves as specified (exactly at tolerance passes, just over fails)
- [ ] an unknown check_code raises

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
