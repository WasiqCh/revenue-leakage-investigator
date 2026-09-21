# TICKET-036 - Clause extraction and evaluation harness

- **Status:** TODO
- **Phase:** 6 - RAG and real data
- **Effort:** 2.0 days
- **Depends on:** TICKET-035, TICKET-027

## Goal

Extract structured commercial terms from contracts and score accuracy against ~30 labelled clauses.

## What this means

Pull the actionable numbers out of legal prose - quantity, price, dates, effective period - then grade ourselves against a frozen set of about 30 clauses where we know the right answer.

## Context

Includes negative items where the correct behaviour is to abstain rather than guess. Correctness is exact match or token-F1 above 0.9, plus a grounding check that the extracted text actually exists in the source.

## Deliverables

- `backend/app/rag/clause_extraction.py`
- `backend/app/eval/suites/clause_extraction.py`
- `fixtures/golden/clauses.json`
- `backend/tests/integration/test_clause_eval.py`

## Acceptance criteria

- [ ] per-field metrics are emitted
- [ ] grounding rate is 1.0 for the scripted mock (no fabricated spans)
- [ ] abstention on the negative items is scored as correct
- [ ] the test set hash matches the frozen value

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
