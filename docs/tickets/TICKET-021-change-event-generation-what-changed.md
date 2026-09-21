# TICKET-021 - Change event generation (what changed)

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.0 day
- **Depends on:** TICKET-005

## Goal

Record field-level diffs across versions of lines, terms and amendments.

## What this means

Not just 'billing says 70' but 'billing was changed to 70 on 3 May by the billing system, while the contract had already been amended to 100 on 1 April'. That sequence is what lets Finance act.

## Context

Diffs slowly-changing-dimension versions of subscription lines, contract terms and amendments, writing change_event rows with changed_by and change_source.

## Deliverables

- `backend/app/changefeed/diff.py`
- `backend/tests/integration/test_change_events.py`

## Acceptance criteria

- [ ] changing a subscription line quantity produces exactly one change_event with correct old and new values
- [ ] re-running produces no duplicate events
- [ ] events are ordered by changed_at

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
