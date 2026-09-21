# TICKET-040 - Ops API and constrained Q&A endpoint

- **Status:** TODO
- **Phase:** 7 - API
- **Effort:** 2.0 days
- **Depends on:** TICKET-037, TICKET-030

## Goal

Trigger runs, expose status, and implement 'ask the investigator' grounded in one case.

## What this means

Buttons to start a detection or investigation run, plus a question box that is strictly limited to the evidence in a single case. If the answer is not in that evidence, it refuses rather than making something up.

## Context

Q&A is scoped to one case's evidence pack, returns citations that resolve to evidence rows, and returns refused=true when unsupported.

## Deliverables

- `backend/app/api/routers/ops.py`
- `backend/app/api/routers/qa.py`
- `backend/app/ai/qa.py`
- `backend/tests/integration/test_qa_grounding.py`

## Acceptance criteria

- [ ] an answerable question returns citations that resolve to evidence rows
- [ ] an unanswerable question returns refused=true with zero fabricated citations
- [ ] Q&A cannot access another case's evidence (scoping test)
- [ ] triggering a reconcile twice is idempotent

## Verification

**Gate G8 — stop here.** Before starting the next ticket, run

```bash
make verify
```

and paste `artifacts/verify-report.md` back. Work does not continue until this
gate is signed off. See [../verification-protocol.md](../verification-protocol.md).

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
