# TICKET-051 - Overview dashboard and analytics

- **Status:** TODO
- **Phase:** 8 - Frontend
- **Effort:** 2.0 days
- **Depends on:** TICKET-041, TICKET-038, TICKET-040

## Goal

Build the landing screen and the analytics screen.

## What this means

This is the first screen anyone sees, including in the demo video. Four headline
numbers at the top — money at risk, confirmed, recovered, and how many cases are
waiting — then charts that answer "where is the money leaking, and why".

Read [`../ux-ui-plan.md`](../ux-ui-plan.md) first. It defines the visual language,
the exact wording for every label, and the layout. This ticket implements it.

## Context

Top cards: potential leakage, confirmed leakage, recovered revenue, open
investigations. Then: leakage trend over time, leakage by root cause, by product,
by customer, high-risk accounts, and detection performance.

**No chart may exist without answering a business question.** If you cannot write
the question a chart answers in one sentence, delete the chart. That rule is from
the specification and it is the difference between a real product and dashboard
clutter.

All numbers come from the API. Nothing is hardcoded or faked — a reviewer will
click through and check.

## Deliverables

- `frontend/app/page.tsx`
- `frontend/app/analytics/page.tsx`
- `frontend/components/metric-card.tsx`
- `frontend/components/leakage-trend-chart.tsx`
- `frontend/components/breakdown-chart.tsx`
- `frontend/components/high-risk-accounts.tsx`

## Acceptance criteria

- [ ] the four headline cards render values from the API
- [ ] a leakage trend chart renders across the 12-month dataset
- [ ] breakdowns render by root cause, product and customer
- [ ] a high-risk accounts list renders, sorted by exposure
- [ ] every number traces to an API response — no hardcoded figures anywhere
- [ ] each chart has a one-sentence business question stated in the code as a comment
- [ ] loading, empty and error states are all designed

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
