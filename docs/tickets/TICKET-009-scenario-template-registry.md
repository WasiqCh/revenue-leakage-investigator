# TICKET-009 - Scenario template registry

- **Status:** TODO
- **Phase:** 2 - Data generation
- **Effort:** 1.0 day
- **Depends on:** TICKET-005

## Goal

Typed definitions for each leakage pattern and each legitimate-exception pattern.

## What this means

Write down, in code, every kind of problem we want the system to find - and every kind of 'this looks wrong but is actually fine' case. This list is the recipe book the fake data is generated from.

## Context

Ten leak types plus at least four exception-only scenarios (approved discount, free pilot, grace period, grandfathered expired discount). Each declares which systems drift, which evidence should exist, and the expected root cause.

## Deliverables

- `backend/app/generate/scenarios.py`
- `backend/tests/unit/test_scenarios.py`

## Acceptance criteria

- [ ] all 10 leak types are present
- [ ] at least 4 exception types are present
- [ ] each spec validates against Pydantic and names its expected evidence set
- [ ] a test asserts the set of leak_type values matches the LeakType enum exactly

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
