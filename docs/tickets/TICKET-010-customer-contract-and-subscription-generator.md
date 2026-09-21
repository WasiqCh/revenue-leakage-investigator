# TICKET-010 - Customer, contract and subscription generator

- **Status:** TODO
- **Phase:** 2 - Data generation
- **Effort:** 1.5 day
- **Depends on:** TICKET-009

## Goal

Seeded generator producing customers, contracts, subscriptions and subscription lines.

## What this means

Generate a realistic fake company from a scenario recipe. Because we generate the data from a known recipe, we automatically know the right answer - which is what makes the testing later possible.

## Context

Same seed always produces identical output. Subscription lines use slowly-changing-dimension versioning so history is preserved. Names are synthetic.

## Deliverables

- `backend/app/generate/core.py`
- `backend/tests/property/test_generator_invariants.py`

## Acceptance criteria

- [ ] same seed produces an identical output hash
- [ ] line effective ranges never overlap within a subscription
- [ ] subscription dates always fall inside contract dates
- [ ] a test asserts generated names match the synthetic pattern (no real companies)

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
