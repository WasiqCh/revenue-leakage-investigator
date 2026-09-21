# TICKET-015 - Expected revenue engine

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.5 day
- **Depends on:** TICKET-014

## Goal

Compute what the customer should have been charged for a given line and period.

## What this means

This is the number everything is measured against: given the contract, its amendments, the price rules and the proration, what should the invoice have said?

## Context

Composes contract terms, amendments, pricing rules, entitlement quantity and proration. Price lookup precedence is by priority then specificity. Critically, this function must never read invoice tables - otherwise it would 'agree' with the very error it is meant to catch.

## Deliverables

- `backend/app/billing/expected_revenue.py`
- `backend/tests/unit/test_expected_revenue.py`

## Acceptance criteria

- [ ] for every generated leak type the engine's expected value matches the manifest
- [ ] a test proves the function never reads invoice or invoice_line (query-log assertion)
- [ ] price precedence is deterministic across shuffled rule insertion order

## Verification

**Gate G3 — stop here.** Before starting the next ticket, run

```bash
make verify
```

and paste `artifacts/verify-report.md` back. Work does not continue until this
gate is signed off. See [../verification-protocol.md](../verification-protocol.md).

---

**Checked individually**, not only at the next gate, because:

- This must never read invoice tables, or it will agree with the error it exists to catch.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
