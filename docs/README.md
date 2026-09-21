# Documentation index

This folder is the full written record of the AI Revenue Leakage Investigator:
what it is, how it is built, why each significant decision was made, and how to
run, demo and repair it.

If you are new here, start with [../README.md](../README.md). It is the single
source of truth and it explains the product in plain English. Then read
[../AGENTS.md](../AGENTS.md) if you are going to write any code — it contains
binding rules, not advice.

---

## What is in this folder

| Document | What it is for | Who should read it |
|---|---|---|
| [PRD.md](PRD.md) | What we are building, for whom, and why. Scope, requirements, and what is explicitly out of scope. | Product owner, reviewer, anyone new to the project |
| [TRD.md](TRD.md) | How it is built: components, data flow, technology choices, interfaces. | Engineers, CTO |
| [architecture.md](architecture.md) | The system drawn out — the pipeline from five source systems to a human decision. | Everyone, at least the first diagram |
| [data-model.md](data-model.md) | Every table, what class of data it holds, and which parts are source data versus derived. | Engineers, reviewers checking the read-only guarantee |
| [billing-periods.md](billing-periods.md) | The hardest part of the domain: date windows, anchors, clamping and proration. | Engineers working on money or dates |
| [confidence.md](confidence.md) | How the confidence score is computed, the eight weighted factors, and the five hard gates. | Product owner, engineers, anyone auditing the "94%" |
| [case-lifecycle.md](case-lifecycle.md) | The state machine: which case states exist and which moves between them are legal. | Engineers, reviewers |
| [evaluation.md](evaluation.md) | How we prove the system works: the golden dataset, the metrics, and the targets. | Product owner, CTO, reviewer |
| [glossary.md](glossary.md) | Plain-English dictionary of every technical term used anywhere in this project. | **Start here if you are not an engineer** |
| [demo-script.md](demo-script.md) | Click-by-click script for recording the two-minute demo video. | Whoever records the demo |
| [runbook.md](runbook.md) | How to start, stop, reset, and repair the system, plus the top five failure modes. | Whoever operates it |
| [adr/](adr/) | One short file per significant decision, each stating the reason it was made. | Reviewers, CTO, future maintainers |
| [tickets/](tickets/) | The 48 units of work the application is built from. Start with [tickets/README.md](tickets/README.md). | Engineers |

Also at the repo root:

- [../README.md](../README.md) — what the product is, in plain English
- [../AGENTS.md](../AGENTS.md) — binding rules for any coding agent
- [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) — the CUAD dataset and its licence position
- [../LICENSE](../LICENSE) — MIT

---

## Suggested reading orders

### (a) For the product owner

You want to understand what the thing does, whether it is credible, and what it
will cost. You do not need to read code.

1. [../README.md](../README.md) — the whole product in one page
2. [glossary.md](glossary.md) — keep this open in a second tab; every term is defined here
3. [PRD.md](PRD.md) — scope, requirements, and what is deliberately excluded
4. [demo-script.md](demo-script.md) — what the recording will show
5. [confidence.md](confidence.md) — why a "94% confident" claim from this system means something, when the same claim from a model would not
6. [evaluation.md](evaluation.md) — how we prove it works, and what the targets are

You can stop there. Everything below is engineering detail.

### (b) For a new engineer

You are going to write code. Read in this order before touching anything.

1. [../README.md](../README.md) — context
2. [../AGENTS.md](../AGENTS.md) — **read this completely before writing any code.** The hard rules in section 1 are not negotiable.
3. [architecture.md](architecture.md) — the shape of the system
4. [TRD.md](TRD.md) — the technical design
5. [data-model.md](data-model.md) — the tables you will be working with
6. [glossary.md](glossary.md) — skim it so nothing surprises you later
7. [tickets/README.md](tickets/README.md) — then start at [TICKET-001](tickets/TICKET-001-repo-scaffold-tooling-and-ci-skeleton.md) and work upwards
8. [billing-periods.md](billing-periods.md) and [confidence.md](confidence.md) — read these *before* you reach TICKET-013 and TICKET-026 respectively
9. [runbook.md](runbook.md) — so you can get yourself unstuck

The single most important thing to internalise: **the AI never computes money,
and the AI never writes to financial data.** If a task seems to require either,
you have misunderstood the task.

### (c) For a reviewer or CTO

You are assessing whether this is credible engineering or a demo. Read these,
in this order, and check the claims.

1. [../README.md](../README.md) — the three rules that make it credible
2. [adr/](adr/) — all nine decision records, in order. Each is short and states its reason.
3. [architecture.md](architecture.md) — particularly the Verifier, which is the component most projects leave out
4. [evaluation.md](evaluation.md) — the metrics and the targets
5. [confidence.md](confidence.md) — how the score is computed and how it is capped
6. [data-model.md](data-model.md) — to check the read-only boundary is structural, not a promise
7. [../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) — the third-party data position
8. [tickets/README.md](tickets/README.md) — to see the work broken down and the effort estimate

Things worth specifically verifying, because they are the claims most easily
faked:

- Can any code path write to an invoice or contract table? (It should be
  impossible via the `rl_readonly` role, and proven by test.)
- Does the LLM emit any stored number? (It should emit text and exactly one
  enum.)
- Does running detection twice create duplicate cases? (It should create zero.)

---

## Architecture decision records

Every locked decision has a record stating the reason it was made. They are
numbered and should be read in order.

| ADR | Decision | Why it matters |
|---|---|---|
| [ADR-001](adr/ADR-001-deterministic-money-no-llm-math.md) | All money is computed in deterministic code, never by the language model | A model cannot be trusted with arithmetic, and an approximate dollar figure is worthless |
| [ADR-002](adr/ADR-002-postgres-pgvector-docker-only.md) | PostgreSQL 16 + pgvector, and Docker is the only supported way to run it | One datastore for records, cases, jobs and vectors; no SQLite fallback to drift from |
| [ADR-003](adr/ADR-003-hand-rolled-agent-loop.md) | A hand-rolled agent loop, not an agent framework | Testable, no framework churn, and a loop we can reason about completely |
| [ADR-004](adr/ADR-004-read-only-role-guardrail.md) | The read-only database role is the guardrail, not the prompt | "Never mutate an invoice" becomes a permission the database enforces, not a promise |
| [ADR-005](adr/ADR-005-postgres-job-queue-not-celery.md) | Background jobs use a Postgres table, not Celery or a message broker | One less piece of infrastructure to run and operate |
| [ADR-006](adr/ADR-006-act-act-proration-half-open-intervals.md) | Half-open billing periods and ACT/ACT proration | The only way to make periods contiguous and non-overlapping, with no double-counted day |
| [ADR-007](adr/ADR-007-cuad-real-data-non-redistribution.md) | CUAD real contracts for retrieval and evaluation, never redistributed | Realistic legal prose and a free answer key, without redistributing data of unclear licence |
| [ADR-008](adr/ADR-008-scenario-seeded-synthetic-data.md) | Synthetic data is generated from labelled scenario templates | We know the right answer by construction, so evaluation is free and exact |
| [ADR-009](adr/ADR-009-cloudflare-ai-search-not-product-path.md) | Cloudflare AI Search is not the product's retrieval path | We considered the managed option, measured it, and documented why we kept our own |

---

## The tickets

The application is built from 48 tickets, TICKET-001 to TICKET-048, in numeric
order. Start with [tickets/README.md](tickets/README.md) for the workflow and the
phase breakdown.

TICKET-048 (the managed-RAG comparison baseline) is **optional** and can be
skipped without breaking anything else.

---

## A note on status

This repository currently contains the specification, the architecture and the
tickets. The application code is built from those tickets. Where a document
describes behaviour, it is describing the specified behaviour — the acceptance
criteria in the corresponding ticket are what prove it was built.
