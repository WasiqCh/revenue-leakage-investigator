# TICKET-044 - Change timeline, recovered-revenue ledger and time-to-detect simulator

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 2.0 days
- **Depends on:** TICKET-042, TICKET-040

## Goal

Three supporting views: what changed, what we recovered, and what faster detection would have saved.

## What this means

The 'what changed' view turns a mismatch into a story with dates. The ledger tracks money actually recovered. The simulator answers 'if we had caught this in month one, how much would we have saved?' - a strong closing beat for a demo.

## Context

Timeline groups events by system with old to new values. Ledger totals must reconcile to the case_outcome sums. Simulator persists its run configuration.

## Deliverables

- `frontend/app/timeline/page.tsx`
- `frontend/app/ledger/page.tsx`
- `frontend/app/simulator/page.tsx`

## Acceptance criteria

- [ ] the timeline groups events by system with correct old to new values
- [ ] the ledger totals recovered vs written-off vs open and reconciles to case_outcome sums
- [ ] re-running the simulator with different parameters produces a different distribution

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
