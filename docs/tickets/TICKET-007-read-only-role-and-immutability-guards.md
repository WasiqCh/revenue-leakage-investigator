# TICKET-007 - Read-only role and immutability guards

- **Status:** TODO
- **Phase:** 1 - Schema
- **Effort:** 0.5 day
- **Depends on:** TICKET-006

## Goal

Provision a SELECT-only database role and add triggers that block edits to audit data.

## What this means

This is the safety gate. The AI connects to the database with an account that is physically unable to change an invoice or a contract - so 'the AI never changes financial data' is a fact enforced by the database, not a promise in a comment.

## Context

Role `rl_readonly` gets SELECT only on source tables. BEFORE UPDATE OR DELETE triggers block writes to audit_event and agent_trace_step, making evidence effectively append-only.

## Deliverables

- `scripts/init_db.sql (role section)`
- `backend/app/db/guards.py`
- `backend/tests/integration/test_immutability.py`

## Acceptance criteria

- [ ] a test connecting as rl_readonly gets 'permission denied' on UPDATE invoice
- [ ] UPDATE audit_event raises
- [ ] the application role can still insert normally
- [ ] no code path grants write access to the agent role

## Verification

**Checked individually**, not only at the next gate, because:

- Guardrail: the agent must be physically unable to write to source tables.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
