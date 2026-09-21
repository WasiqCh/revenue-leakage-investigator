# TICKET-043 - Case detail UI

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 2.0 days
- **Depends on:** TICKET-042, TICKET-039

## Goal

The single most important screen: chain of evidence, report, trace and decision panel.

## What this means

Where a human decides. Shows the contract-to-mismatch chain visually, every piece of evidence with a clickable excerpt, the AI's step-by-step trace, and approve or reject with a confirmation step.

## Context

Every citation renders an excerpt with its source label. Approve/reject round-trips to the API without a page reload. Viewers see disabled actions.

## Deliverables

- `frontend/app/cases/[id]/page.tsx`
- `frontend/components/evidence-chain.tsx`
- `frontend/components/agent-trace.tsx`
- `frontend/components/decision-panel.tsx`

## Acceptance criteria

- [ ] every citation renders an excerpt with its source label
- [ ] the trace shows phases and tool calls in order
- [ ] approve/reject round-trips to the API and updates the badge without a reload
- [ ] a viewer sees disabled actions

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
