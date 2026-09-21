# TICKET-025 - Exception registry and triage lookup

- **Status:** TODO
- **Phase:** 4 - Cases and money
- **Effort:** 1.0 day
- **Depends on:** TICKET-006

## Goal

Store approved exceptions with scope and validity dates, and look them up during triage.

## What this means

A first-class list of 'this customer is allowed to be different' - an approved discount, a free pilot, a grace period. When a mismatch matches one of these, the system closes it as a valid exception without wasting an AI investigation.

## Context

Scope matching across customer / subscription / subscription_line / product / global, combined with period overlap. Expired exceptions do not match.

## Deliverables

- `backend/app/cases/exceptions.py`
- `backend/tests/unit/test_exception_lookup.py`

## Acceptance criteria

- [ ] an exception covering the period routes the case to VALID_EXCEPTION with zero LLM calls
- [ ] an expired exception (effective_to before period_start) does not match
- [ ] a global-scope exception matches all customers

## Verification

**Gate G5 — stop here.** Before starting the next ticket, run

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
