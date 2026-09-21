# TICKET-022 - Case fingerprinting and idempotent upsert

- **Status:** TODO
- **Phase:** 4 - Cases and money
- **Effort:** 1.0 day
- **Depends on:** TICKET-016

## Goal

Collapse a repeating mismatch into one case with an affected-period range.

## What this means

If the same 30-seat gap persists for five months, that is one ongoing problem, not five separate tickets. Without this the review queue becomes unusable and Finance stops reading it.

## Context

case_key is a deterministic hash over (customer, subscription_line, leak_type, product) that intentionally ignores the period. Upsert extends the affected range and appends case_period rows.

## Deliverables

- `backend/app/cases/fingerprint.py`
- `backend/tests/integration/test_case_dedup.py`

## Acceptance criteria

- [ ] a mismatch persisting 5 periods yields exactly one case with affected_period_count == 5
- [ ] re-running detection leaves the case count unchanged
- [ ] two different leak types on the same line yield two cases

## Verification

**Checked individually**, not only at the next gate, because:

- Without this the case queue fills with duplicates and Finance stops reading it.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
