# TICKET-029 - Bounded agent loop

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 2.0 days
- **Depends on:** TICKET-028

## Goal

Implement the plan, gather, hypothesise, test, conclude loop with budgets.

## What this means

The AI investigator works in a loop with a strict spending limit on tool calls and tokens, and every step is written down. An investigation that cannot finish does not run forever - it stops and says so.

## Context

Persists every step into agent_trace_step and manages the investigation_run lifecycle with a terminal_reason.

## Deliverables

- `backend/app/ai/agent_loop.py`
- `backend/tests/unit/test_agent_loop.py`

## Acceptance criteria

- [ ] a scripted mock that never concludes terminates at budget_exhausted
- [ ] every step is persisted with an incrementing step_index
- [ ] the loop never exceeds the configured tool-call budget
- [ ] the loop makes no writes to source tables

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
