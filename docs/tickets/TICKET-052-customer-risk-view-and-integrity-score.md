# TICKET-052 - Customer risk view and Revenue Integrity Score

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 1.5 day
- **Depends on:** TICKET-038, TICKET-026

## Goal

A per-customer screen showing revenue health, plus the computed Revenue Integrity
Score.

## What this means

One page per customer answering: how much are they supposed to be paying, how much
are we actually invoicing, how big is the gap, and how much can we trust their data?

The score is a **0–100 operational hint**, not a financial statement. It must be
labelled as internal and non-authoritative everywhere it appears — otherwise Finance
will treat a heuristic as audited fact, which is exactly the kind of thing that gets
a system like this turned off.

Read [`../ux-ui-plan.md`](../ux-ui-plan.md) for layout and wording.

## Context

Per customer: current ARR, contracted ARR, billed ARR, potential leakage, leakage
percentage, open cases, historical cases, products, contracts, billing health.

The score is broken into five labelled components so a user can see *why* it is low:

- Contract integrity
- Billing integrity
- Usage alignment
- Data completeness
- Open exceptions

The score is **deterministic and computed in code** (like confidence). The AI
contributes nothing to it.

## Deliverables

- `frontend/app/customers/[id]/page.tsx`
- `frontend/components/integrity-score.tsx`
- `backend/app/cases/integrity_score.py`
- `backend/tests/unit/test_integrity_score.py`

## Acceptance criteria

- [ ] the page shows current, contracted and billed ARR side by side
- [ ] the score renders with all five component breakdowns visible
- [ ] the score is labelled an internal operational metric, not an audited figure
- [ ] the score is deterministic — identical inputs give identical output
- [ ] the score is computed without any LLM call
- [ ] open and historical cases are listed for the customer

## Verification

**Gate G11 — stop here.** Before starting the next ticket, run

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
