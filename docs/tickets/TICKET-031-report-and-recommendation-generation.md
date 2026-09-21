# TICKET-031 - Report and recommendation generation

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 1.5 day
- **Depends on:** TICKET-030

## Goal

Produce the investigation report and the correction proposal.

## What this means

Write the human-readable case file: what happened, why, what it is worth, what Finance should do - with a citation on every claim.

## Context

The report schema deliberately has no numeric fields for the LLM to fill in. The model supplies narrative plus one qualitative factor (contract_clarity). The recommendation always carries requires_human_approval = true.

## Deliverables

- `backend/app/ai/report.py`
- `backend/app/ai/prompts/investigate.md`
- `backend/tests/unit/test_report.py`

## Acceptance criteria

- [ ] the report schema rejects any numeric field emitted by the LLM
- [ ] exactly one qualitative factor is accepted
- [ ] the recommendation is never auto-approved
- [ ] the narrative contains inline citation markers that resolve to evidence rows

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
