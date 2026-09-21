# Implementation tickets

**48 tickets.** Each one is a self-contained unit of work with its own file.
Work them in numeric order — dependencies are already ordered, so a ticket only
ever depends on earlier ones.

---

## What this means

These are the building instructions. Each ticket describes one small piece: what to
build, which files to create, and a checklist that proves it works. An engineer —
or an AI agent — works through them top to bottom and the product appears at the
end.

Every ticket has the same shape:

| Section | What it tells you |
|---|---|
| **Goal** | One sentence: what this ticket achieves |
| **What this means** | Plain English. No jargon without explanation |
| **Context** | The technical detail needed to actually build it |
| **Deliverables** | Exactly which files to create |
| **Acceptance criteria** | A checklist. The ticket is done when every box is ticked |
| **Definition of done** | Process requirements that apply to every ticket |

---

## Rules

1. Read [`../../AGENTS.md`](../../AGENTS.md) before starting. Its rules are binding.
2. One ticket at a time. Finish and verify it before moving on.
3. Create only the files the ticket names. Do not reorganise the repository.
4. When done: tick every acceptance criterion, set `Status: DONE` in the ticket
   file, and confirm `make test` passes.
5. Commit with the ticket number in the subject and the co-author trailer:

```
TICKET-014: implement proration engine

Refs: docs/tickets/TICKET-014-proration-engine.md

Co-authored-by: umer-ch817 <chumerha91@gmail.com>
```

The `Co-authored-by:` line is **required on every commit**.

---

## Phases

| Phase | Tickets | Topic | Est. |
|---|---|---|---|
| 0 | 001–004 | Foundation — repo, Docker, settings, database plumbing | 2.5 d |
| 1 | 005–008 | Schema — source tables, derived tables, guardrails, money types | 4.5 d |
| 2 | 009–012 | Data generation — scenario recipes, generators, golden labels | 5.0 d |
| 3 | 013–021 | Deterministic core — periods, proration, detectors, entity resolution | 12.5 d |
| 4 | 022–026 | Cases and money — dedup, state machine, leakage maths, confidence | 6.0 d |
| 5 | 027–032 | AI layer — provider, tools, agent loop, verifier, jobs | 10.0 d |
| 6 | 033–036 | RAG and real data — CUAD, chunking, retrieval, clause extraction | 6.0 d |
| 7 | 037–040 | API — FastAPI, cases, decisions, ops, constrained Q&A | 5.5 d |
| 8 | 041–044 | Frontend — scaffold, case queue, case detail, supporting views | 6.5 d |
| 9 | 045–048 | Evaluation — golden harness, e2e, optional baseline, docs | 6.5 d |
| | | **Total** | **~65 d** |

These are deliberately conservative solo estimates. They are a planning aid, not a
promise. Several tickets are small for an experienced implementer.

### Dependency spine

The critical path:

```
001 → 004 → 006 → 008 → 015 → 016 → 022 → 026 → 029 → 030 → 037 → 040 → 045 → 046
```

**Data generation (009–012) and the deterministic core (013–026) must land before
any AI-facing ticket.** Building the agent first is the most common mistake here —
there is nothing for it to investigate, and no way to tell whether its answers are
right.

---

## If time is short

Build in this order and stop wherever time runs out — each cut point leaves a
coherent, demoable system:

1. **Phases 0–2** — the system has realistic data and a database.
2. **Phase 3** — discrepancies are being detected. *This alone is genuinely useful.*
3. **Phase 4** — cases are deduplicated, scored and routable.
4. **Phases 5 + 8** — the agent investigates and Finance can review. **The hero
   scenario works end to end here.**
5. **Phases 6, 7, 9** — real contract text, API completeness, and the evaluation
   scorecard that proves it all works.

**TICKET-048 is optional.** It compares our search against a managed service for
measurement only. Skipping it breaks nothing.

---

## Ticket list

### Phase 0 — Foundation
- [TICKET-001](TICKET-001-repo-scaffold-tooling-and-ci-skeleton.md) — Repo scaffold, tooling and CI skeleton
- [TICKET-002](TICKET-002-docker-compose-stack.md) — Docker Compose stack
- [TICKET-003](TICKET-003-settings-and-environment-contract.md) — Settings and environment contract
- [TICKET-004](TICKET-004-database-engine-session-and-model-conventions.md) — Database engine, session and model conventions

### Phase 1 — Schema
- [TICKET-005](TICKET-005-source-domain-schema-and-migration.md) — Source-domain schema and migration
- [TICKET-006](TICKET-006-derived-case-and-ops-schema-and-migration.md) — Derived, case and ops schema and migration
- [TICKET-007](TICKET-007-read-only-role-and-immutability-guards.md) — Read-only role and immutability guards
- [TICKET-008](TICKET-008-money-and-interval-primitives.md) — Money and interval primitives

### Phase 2 — Data generation
- [TICKET-009](TICKET-009-scenario-template-registry.md) — Scenario template registry
- [TICKET-010](TICKET-010-customer-contract-and-subscription-generator.md) — Customer, contract and subscription generator
- [TICKET-011](TICKET-011-usage-invoice-and-billing-generators-with-injected-d.md) — Usage, invoice and billing generators with injected drift
- [TICKET-012](TICKET-012-ground-truth-manifests-golden-labels-and-seed-comman.md) — Ground-truth manifests, golden labels and seed command

### Phase 3 — Deterministic core
- [TICKET-013](TICKET-013-billing-period-engine.md) — Billing period engine
- [TICKET-014](TICKET-014-proration-engine.md) — Proration engine
- [TICKET-015](TICKET-015-expected-revenue-engine.md) — Expected revenue engine
- [TICKET-016](TICKET-016-detector-framework-and-idempotent-persistence.md) — Detector framework and idempotent persistence
- [TICKET-017](TICKET-017-detectors-batch-1.md) — Detectors batch 1
- [TICKET-018](TICKET-018-detectors-batch-2.md) — Detectors batch 2
- [TICKET-019](TICKET-019-period-boundary-to-dollar-conversion-and-double-bill.md) — Period-boundary to dollar conversion and double-billing
- [TICKET-020](TICKET-020-entity-resolution.md) — Entity resolution
- [TICKET-021](TICKET-021-change-event-generation-what-changed.md) — Change event generation (what changed)

### Phase 4 — Cases and money
- [TICKET-022](TICKET-022-case-fingerprinting-and-idempotent-upsert.md) — Case fingerprinting and idempotent upsert
- [TICKET-023](TICKET-023-case-lifecycle-state-machine.md) — Case lifecycle state machine
- [TICKET-024](TICKET-024-leakage-maths-and-fx-normalisation.md) — Leakage maths and FX normalisation
- [TICKET-025](TICKET-025-exception-registry-and-triage-lookup.md) — Exception registry and triage lookup
- [TICKET-026](TICKET-026-confidence-engine.md) — Confidence engine

### Phase 5 — AI layer
- [TICKET-027](TICKET-027-llm-provider-adapter-mock-provider-and-call-ledger.md) — LLM provider adapter, mock provider and call ledger
- [TICKET-028](TICKET-028-read-only-tool-registry.md) — Read-only tool registry
- [TICKET-029](TICKET-029-bounded-agent-loop.md) — Bounded agent loop
- [TICKET-030](TICKET-030-verifier.md) — Verifier
- [TICKET-031](TICKET-031-report-and-recommendation-generation.md) — Report and recommendation generation
- [TICKET-032](TICKET-032-postgres-job-queue-and-worker-loop.md) — Postgres job queue and worker loop

### Phase 6 — RAG and real data
- [TICKET-033](TICKET-033-cuad-downloader-cache-offline-fixture-and-licence-no.md) — CUAD downloader, cache, offline fixture and licence notice
- [TICKET-034](TICKET-034-cuad-mapping-clause-chunking-and-indexes.md) — CUAD mapping, clause chunking and indexes
- [TICKET-035](TICKET-035-hybrid-retrieval-with-reciprocal-rank-fusion.md) — Hybrid retrieval with reciprocal rank fusion
- [TICKET-036](TICKET-036-clause-extraction-and-evaluation-harness.md) — Clause extraction and evaluation harness

### Phase 7 — API
- [TICKET-037](TICKET-037-fastapi-skeleton-seeded-roles-and-error-model.md) — FastAPI skeleton, seeded roles and error model
- [TICKET-038](TICKET-038-cases-api.md) — Cases API
- [TICKET-039](TICKET-039-decision-api.md) — Decision API
- [TICKET-040](TICKET-040-ops-api-and-constrained-qa-endpoint.md) — Ops API and constrained Q&A endpoint

### Phase 8 — Frontend
- [TICKET-041](TICKET-041-nextjs-scaffold-api-client-and-role-switcher.md) — Next.js scaffold, API client and role switcher
- [TICKET-042](TICKET-042-case-queue-ui.md) — Case queue UI
- [TICKET-043](TICKET-043-case-detail-ui.md) — Case detail UI
- [TICKET-044](TICKET-044-change-timeline-recovered-revenue-ledger-and-time-to.md) — Change timeline, recovered-revenue ledger and time-to-detect simulator

### Phase 9 — Evaluation
- [TICKET-045](TICKET-045-golden-evaluation-harness.md) — Golden evaluation harness
- [TICKET-046](TICKET-046-end-to-end-pipeline-test-and-property-suite.md) — End-to-end pipeline test and property suite
- [TICKET-047](TICKET-047-documentation-adrs-licence-notices-and-runbook.md) — Documentation, ADRs, licence notices and runbook
- [TICKET-048](TICKET-048-managed-rag-comparison-baseline-cloudflare-ai-search.md) — Managed-RAG comparison baseline *(optional)*
