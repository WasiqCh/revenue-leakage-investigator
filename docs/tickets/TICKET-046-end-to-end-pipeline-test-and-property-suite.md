# TICKET-046 - End-to-end pipeline test and property suite

- **Status:** TODO
- **Phase:** 9 - Evaluation
- **Effort:** 2.0 days
- **Depends on:** TICKET-040, TICKET-045

## Goal

A full run from empty database to approved case, plus consolidated invariant tests.

## What this means

One test that does the whole journey end to end with no network: generate data, detect, investigate, approve, check the ledger. Proves the pieces actually fit together, not just that each works alone.

## Context

Plus the consolidated Hypothesis suite covering interval additivity, money conservation and confidence determinism.

## Deliverables

- `backend/tests/e2e/test_full_pipeline.py`
- `backend/tests/property/test_invariants.py`

## Acceptance criteria

- [ ] the e2e test passes with zero network access
- [ ] the e2e test asserts one case per injected leak with correct amounts
- [ ] property tests cover interval additivity, money conservation and confidence determinism
- [ ] the suite runs within the CI timeout

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
