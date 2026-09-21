# TICKET-028 - Read-only tool registry

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 1.5 day
- **Depends on:** TICKET-007, TICKET-027

## Goal

Define the investigation tools the agent may call, all read-only and evidence-producing.

## What this means

Give the AI a fixed set of questions it is allowed to ask (fetch this contract clause, fetch these invoice lines). It cannot ask anything else, cannot write anything, and each answer is recorded so it can be cited later.

## Context

Each tool has a Pydantic argument schema, a hard row cap, and normalises its results into evidence rows carrying source_table and source_pk.

## Deliverables

- `backend/app/ai/tools.py`
- `backend/tests/unit/test_tools.py`
- `backend/tests/integration/test_tool_evidence.py`

## Acceptance criteria

- [ ] every tool only issues SELECT statements (query-log assertion)
- [ ] results above the row cap are truncated deterministically
- [ ] each tool call can produce a citable evidence row with source_table and source_pk

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
