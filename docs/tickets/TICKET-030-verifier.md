# TICKET-030 - Verifier

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 2.0 days
- **Depends on:** TICKET-029, TICKET-026

## Goal

Re-check every numeric claim in the agent's report against the database.

## What this means

The most important safety component in the whole system. After the AI writes its report, code goes through every number and checks it against the real records. Anything invented is dropped, and the case is downgraded to needs-review.

## Context

Re-fetches every cited evidence source, validates every numeric claim, emits a verifier_report that drives the confidence gates.

## Deliverables

- `backend/app/ai/verifier.py`
- `backend/tests/unit/test_verifier.py`
- `backend/tests/integration/test_verifier_grounding.py`

## Acceptance criteria

- [ ] a report with a fabricated amount is rejected and caps confidence at 60
- [ ] a report citing a non-existent evidence row fails
- [ ] a fully grounded report passes
- [ ] the verifier is deterministic given the same database state

## Verification

**Gate G6 — stop here.** Before starting the next ticket, run

```bash
make verify
```

and paste `artifacts/verify-report.md` back. Work does not continue until this
gate is signed off. See [../verification-protocol.md](../verification-protocol.md).

---

**Checked individually**, not only at the next gate, because:

- This is what stops invented numbers reaching Finance.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
