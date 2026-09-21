# TICKET-026 - Confidence engine

- **Status:** TODO
- **Phase:** 4 - Cases and money
- **Effort:** 1.5 day
- **Depends on:** TICKET-024, TICKET-006

## Goal

Compute the confidence score from weighted factors plus hard gates.

## What this means

Trust must be earned and measured, not asserted. The AI is allowed to contribute exactly one thing - how clearly the contract is worded. Everything else is measured from data, and hard rules can only ever lower the score.

## Context

Eight weighted factors plus five gates. See docs/confidence.md for the exact weights and the gate behaviour.

## Deliverables

- `backend/app/cases/confidence.py`
- `backend/tests/unit/test_confidence.py`
- `backend/tests/property/test_confidence_determinism.py`

## Acceptance criteria

- [ ] identical inputs produce an identical score
- [ ] a verifier failure caps the score at 60
- [ ] a missing required evidence type caps it at 74
- [ ] a clean deterministic case floors at 85
- [ ] band boundaries at 75 and 90 behave exactly as specified

## Verification

**Checked individually**, not only at the next gate, because:

- Trust must be measured, not asserted by the model.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
