# Frontend

Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui.

## Status

Not yet implemented. Design is in [`../docs/TRD.md`](../docs/TRD.md); the work is
in TICKET-041 through TICKET-044.

## What this means

This is the website Finance uses. It has exactly one job: let a person decide
whether a flagged revenue gap is real, quickly and with confidence.

## Design rules

The product must look like **serious enterprise finance software**, not an AI demo.

Do:
- clean typography, generous spacing, clear hierarchy
- subtle borders, professional tables, compact data visualisations
- status badges, evidence cards, timeline components, side panels
- obvious labels — a viewer watching a recorded demo should never wonder what a
  thing is

Do not:
- neon, glowing gradients, or "AI startup landing page" aesthetics
- a chatbot as the primary interface
- robot illustrations or generic AI icons
- dashboard clutter or unnecessary animation

Reference point: Stripe's dashboard or a modern revenue-operations tool. Not a
model showcase.

## Screens

| Route | Purpose | Ticket |
|---|---|---|
| `/` | Overview: totals, trend, high-risk accounts, queue preview | TICKET-042 |
| `/cases` | Case queue with filters | TICKET-042 |
| `/cases/[id]` | **The most important screen** — evidence chain, report, trace, decision | TICKET-043 |
| `/timeline` | "What changed?" field-level diffs by system | TICKET-044 |
| `/ledger` | Recovered revenue | TICKET-044 |
| `/simulator` | Time-to-detect: what faster detection would have saved | TICKET-044 |

## Rules

- The API client in `lib/api.ts` is typed against the generated OpenAPI schema.
  No `any`.
- Role switching (`viewer`, `finance_analyst`, `finance_approver`) is seeded, not
  real authentication. A viewer must see disabled approve/reject actions.
- Every citation must render its source label and excerpt.
- Empty, loading and error states are all designed — they are not afterthoughts.

## Running

From the repo root, always through Docker:

```bash
make up      # http://localhost:3000
make logs
```
