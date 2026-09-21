# Technical Requirements Document — AI Revenue Leakage Investigator

## What this means

This document is the engineering plan: which technologies we use, how the pieces
fit together, and the rules that keep the system safe and testable.

The central engineering idea is **use the right tool for each job**. Arithmetic is
done by code because code is exact. Reading lawyer-written contract prose is done
by a language model because language models are good at that. Mixing the two up is
the single most common way these systems go wrong, so the boundary is enforced in
code and by database permissions, not by convention.

---

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 15 (App Router), TypeScript (strict), Tailwind, shadcn/ui | Server components, strong typing, enterprise-grade component primitives |
| Backend | Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic | Best-in-class typed validation; the ecosystem for data and AI work |
| Database | PostgreSQL 16 + pgvector | One datastore for relational data **and** vector search. Avoids running a separate vector database |
| Jobs | Postgres `job` table + worker using `FOR UPDATE SKIP LOCKED` | No Redis, no Celery. One less service to run and debug |
| LLM | OpenAI-compatible endpoint via a thin adapter | Provider-independent; configured entirely by environment variables |
| Embeddings | Pluggable; default `text-embedding-3-small`, 1536 dimensions | Swappable without code change |
| Agent | Hand-rolled Python loop | Full control over the trace, budgets and failure modes. No framework churn |
| Tests | pytest, Hypothesis (property-based) | Money and date logic need invariant testing, not example testing |
| Containers | Docker Compose | Docker is the only supported way to run this project |

### Deliberately absent

| Not used | Reason |
|---|---|
| LangChain / LangGraph / PydanticAI / LlamaIndex / CrewAI | The agent loop is ~300 lines and fully testable. A framework adds indirection and version churn for no gain here |
| n8n | Adds a second runtime and an untestable layer for logic that belongs in code |
| Celery / Redis / RabbitMQ / Kafka | The workload is tens of jobs, not millions. A Postgres table is sufficient and simpler |
| SQLite or any non-Docker database path | One supported path means every developer and CI runs the same thing |
| Isolation Forest / Local Outlier Factor | At 50–100 customers, rules and statistics are more accurate **and** explainable, which matters more |
| Fine-tuning | We retrieve and read. Nothing is trained |

---

## 2. Services

```
docker compose
├── db        PostgreSQL 16 + pgvector, pg_trgm, pgcrypto
├── backend   FastAPI  — REST API, orchestration, detection
├── worker    Background investigations (same image, different entrypoint)
└── frontend  Next.js
```

`db` has a healthcheck; `backend` and `worker` wait for it. `frontend` waits for
`backend`.

---

## 3. Backend module layout

```
backend/app/
├── config.py              Typed settings (Pydantic Settings)
├── db/                    engine, session, base, custom types, enums, guards
├── models/                source/  derived/  case/  ops/
├── money/                 DecimalMoney, interval algebra, FX
├── billing/               periods, proration, expected_revenue
├── detect/                framework, checks/*, entity_resolution
├── changefeed/            diff → change_event
├── cases/                 fingerprint, state, leakage, confidence, exceptions
├── ai/                    provider, tools, agent_loop, verifier, report, qa, prompts/
├── rag/                   cuad_adapter, cuad_mapper, chunking, embeddings,
│                          retrieval, clause_extraction
├── jobs/                  queue, worker
├── eval/                  harness, suites/*
├── api/                   main, deps, errors, routers/*
└── cli.py                 seed, reconcile, investigate, eval
```

**Boundary rule:** nothing in `ai/` may import anything from `money/` or
`billing/` and reimplement it. The agent calls tools; tools call the deterministic
modules. A test asserts that no numeric output reaches storage without passing
through `ai/verifier.py`.

---

## 4. Data separation

Five classes of data are kept physically distinct. This is a security and
auditability boundary, not just tidiness.

| Class | Meaning | Written by | Readable by agent |
|---|---|---|---|
| **SRC** | Raw records exactly as external systems report them | Ingestion | Yes (read-only) |
| **NORM** | Canonical entities after entity resolution | Normalization | Yes |
| **DERIV** | Computed: billing periods, reconciliation results | Detection | Yes |
| **CASE** | Investigation state, evidence, recommendations | System + agent | No (agent uses tools) |
| **AI** | Model output: narratives, trace steps | Agent | n/a |
| **HUM** | Human decisions: approvals, rejections, outcomes | Humans | No |
| **OPS** | Jobs, LLM call ledger, eval results | Infrastructure | No |

The agent connects as `rl_readonly`, which holds `SELECT` on SRC/NORM/DERIV only.
**No code path grants it write access to anything.** A test proves this.

---

## 5. API surface

```
GET    /healthz
GET    /customers
GET    /customers/{id}
GET    /customers/{id}/risk
GET    /contracts/{id}
GET    /contracts/{id}/clauses
GET    /reconciliation?customer=&period=&check_code=
GET    /investigations?status=&leak_type=&confidence_band=&customer=&from=&to=
GET    /investigations/{id}
GET    /investigations/{id}/evidence
GET    /investigations/{id}/timeline
GET    /investigations/{id}/trace
POST   /investigations/{id}/investigate
POST   /investigations/{id}/approve
POST   /investigations/{id}/reject
POST   /investigations/{id}/request-review
POST   /investigations/{id}/assign
POST   /investigations/{id}/notes
GET    /analytics/revenue-leakage
GET    /ledger/recovered
GET    /simulator/time-to-detect
POST   /qa/ask
GET    /evaluation
GET    /evaluation/runs
POST   /ops/reconcile
POST   /ops/investigate
GET    /ops/jobs/{id}
```

Conventions: uniform error envelope, cursor or offset pagination, stable default
sort, OpenAPI generated and validated in CI.

Seeded roles (`viewer`, `finance_analyst`, `finance_approver`) are supplied by
header and exist only to demonstrate permissioning. **This is not authentication.**

---

## 6. The agent

```
Plan → Gather → Hypothesize → Test → Conclude
```

- **Bounded:** hard caps on tool calls, tokens and wall-clock time
- **Tool-only:** every fact comes from a registered read-only tool; results become
  citable evidence rows with `source_table` + `source_pk`
- **Traced:** every step is persisted to `agent_trace_step` in order
- **Verified:** after the report is written, `ai/verifier.py` re-fetches every
  cited source and re-checks every numeric claim. Unsupported claims are dropped;
  the case drops to `NEEDS_REVIEW`

Terminal reasons are explicit: `concluded`, `budget_exhausted`,
`insufficient_evidence`, `conflicting_evidence`, `valid_exception`.

---

## 7. RAG pipeline

```
documents → parsing → clause-level chunking → metadata → embeddings
          → pgvector + Postgres full-text → hybrid retrieval (RRF)
          → context assembly → LLM reasoning with citations
```

- Chunking is **clause-level**, not fixed-size, so a citation points at a specific
  sentence rather than "somewhere on page 4"
- Metadata: `customer_id`, `contract_id`, `document_type`, `document_version`,
  `effective_date`, `section`, `page`, `amendment_id` — all filterable
- Hybrid: pgvector cosine similarity fused with `tsvector` ranking using
  **reciprocal rank fusion**
- Every retrieved chunk carries its citation metadata into the prompt so the model
  can cite, and so the verifier can check

---

## 8. Correctness requirements

| Requirement | How it is enforced |
|---|---|
| Money is exact | `Decimal` only. A test fails if a float appears in money modules |
| Deterministic | No unseeded randomness, no wall-clock reads in money or period logic |
| Idempotent | Natural-key upserts; `case_key` dedup; tested by running twice |
| Immutable evidence | Triggers block UPDATE/DELETE on `audit_event` and `agent_trace_step` |
| No financial mutation | Read-only DB role; enforced by test |
| Grounded output | Verifier rejects any claim not backed by a tool result |

---

## 9. Testing strategy

| Level | Scope | Tool |
|---|---|---|
| Unit | Money, intervals, proration, confidence, state machine | pytest |
| Property | Interval additivity, money conservation, confidence determinism | Hypothesis |
| Integration | Schema migrations, detectors, job queue, API | pytest + Postgres |
| End-to-end | seed → reconcile → investigate → approve → ledger | pytest, `LLM_MOCK=1` |
| Evaluation | Detection, exceptions, calibration, clause extraction, RAG | `app/eval/` |

**No test ever touches the network.** All LLM interaction goes through
`MockProvider` with `LLM_MOCK=1`.

---

## 10. Configuration

Everything comes from environment variables validated by a typed `Settings`
object; the app fails fast on missing required values. See `.env.example`.

Critical values: database URL, LLM base URL / key / model, reporting currency,
money tolerances, confidence weights, agent budgets, CUAD cache and offline flags.

---

## 11. Non-functional requirements

| Area | Requirement |
|---|---|
| Performance | Case list < 500 ms; a full reconcile over 100 customers < 60 s; one investigation < 30 s |
| Observability | Structured JSON logs; every LLM call recorded with token counts |
| Auditability | Any case can be fully reconstructed from the audit trail |
| Portability | `docker compose up` on a clean machine with only Docker installed |
| Cost control | Token accounting per call; budgets per investigation |

---

## 12. Production considerations (documented, not built)

If this were deployed for real: role-based access control, encryption at rest and
in transit, secret management, PII handling, tenant isolation, centralized logging
and metrics, backup and restore, and SOC2-style change control. These are called
out so a reviewer knows they were considered — they are deliberately out of scope
for this build (see ADR-002 and §4 of the PRD).

---

## 13. Decision records

| ADR | Decision |
|---|---|
| 001 | Deterministic money — the LLM never computes financial values |
| 002 | PostgreSQL + pgvector, Docker only |
| 003 | Hand-rolled agent loop, no agent framework |
| 004 | Read-only database role as the guardrail |
| 005 | Postgres job queue instead of Celery/Redis |
| 006 | ACT/ACT proration over half-open intervals |
| 007 | CUAD real data, cached outside the repo, never redistributed |
| 008 | Scenario-seeded synthetic data for free ground truth |
| 009 | Cloudflare AI Search rejected for the product path, kept as a baseline |

Full text in [`docs/adr/`](adr/).
