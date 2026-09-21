# TICKET-027 - LLM provider adapter, mock provider and call ledger

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 1.5 day
- **Depends on:** TICKET-003, TICKET-006

## Goal

A single OpenAI-compatible client with retries, structured output and a mock for tests.

## What this means

One front door for all AI calls, configured by environment variables so any compatible provider can be swapped in. Every call is logged with its token cost, and tests use a stand-in that never touches the network.

## Context

Timeouts, bounded retries, JSON-mode structured output, token accounting into llm_call, and an in-process MockProvider.

## Deliverables

- `backend/app/ai/provider.py`
- `backend/app/ai/prompts/`
- `backend/tests/unit/test_provider.py`

## Acceptance criteria

- [ ] all tests run with MockProvider and zero network calls
- [ ] a forced server error triggers exactly the configured number of retries
- [ ] every call writes one llm_call row with token counts
- [ ] malformed JSON output raises a typed error

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
