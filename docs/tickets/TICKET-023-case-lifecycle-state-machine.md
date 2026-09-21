# TICKET-023 - Case lifecycle state machine

- **Status:** TODO
- **Phase:** 4 - Cases and money
- **Effort:** 1.0 day
- **Depends on:** TICKET-022

## Goal

Implement the allowed transitions between case states with actor validation.

## What this means

A strict map of how a case may move - detected, investigated, awaiting review, approved, rejected. Illegal moves are rejected, and every move is recorded.

## Context

Single transition() function with an allowed-edge table, actor type checks and audit emission. See docs/case-lifecycle.md.

## Deliverables

- `backend/app/cases/state.py`
- `backend/tests/unit/test_state_machine.py`
- `backend/tests/property/test_state_machine.py`

## Acceptance criteria

- [ ] Hypothesis proves no reachable illegal state
- [ ] every legal edge is exercisable in tests
- [ ] every transition writes exactly one audit_event
- [ ] APPROVED can only be entered when actor_type is 'human'

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
