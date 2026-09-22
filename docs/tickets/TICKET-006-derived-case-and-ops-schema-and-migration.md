# TICKET-006 - Derived, case and ops schema and migration

- **Status:** DONE
- **Phase:** 1 - Schema
- **Effort:** 1.5 day
- **Depends on:** TICKET-005

## Goal

All remaining tables, plus the pgvector index and full-text index.

## What this means

Create the tables the system itself produces: billing periods, reconciliation results, investigation cases, evidence, audit events and job bookkeeping.

## Context

Tables: billing_period, reconciliation_run, reconciliation_result, case, case_period, evidence, investigation_run, investigation_report, recommendation, agent_trace_step, audit_event, case_outcome, approved_exception, change_event, entity_resolution_match, golden_label, job, llm_call, eval_run, eval_result, qa_message. pgvector index on contract_clause.embedding, GIN index on tsv.

## Deliverables

- [x] `backend/app/models/derived/` (`billing_period.py`,
      `entity_resolution.py`, `reconciliation_result.py`)
- [x] `backend/app/models/case/` (`case.py`, `evidence.py`,
      `investigation.py`, `outcome.py`)
- [x] `backend/app/models/ops/` (`run.py`, `audit.py`, `job.py`,
      `evaluation.py`)
- [x] one Alembic revision
      (`backend/alembic/versions/20260922_0143_e0bf8ae51a4f_derived_case_and_ops_schema.py`)
- [x] `backend/tests/integration/test_schema_derived.py`

## Acceptance criteria

- [x] migration up / down / up succeeds
      (real `alembic upgrade head`, `downgrade base`, `upgrade head`)
- [x] `case.case_key` is unique
      (`test_case_key_is_unique` performs duplicate INSERTs)
- [x] `reconciliation_result` is unique on (run_id, customer, line, period, check_code)
      (`test_reconciliation_result_natural_key_is_unique`)
- [x] EXPLAIN on a vector similarity query uses the vector index
      (`test_explain_uses_the_vector_index` inserts 2,500 deterministic 1536-dimension
      probes, ANALYZEs the table, and asserts the planner chooses
      `ix_contract_clause_embedding` with an Index Scan)

## Verification

**Gate G1 evidence (2026-09-22).** `make` is unavailable in this Windows
sandbox, so every command from its `verify` target was run directly in its
listed order. The current results are recorded in `artifacts/verify-report.md`.

| Check | Result |
|---|---|
| services | pass — backend, db, worker healthy; frontend restarted after its build and was serving route smoke requests |
| migrations up / down / up | pass — full downgrade to base, then both revisions re-applied |
| tests collected | pass — suite collected successfully |
| backend tests | pass — 57 passed, 1 skipped |
| ruff check + format | pass — 45 files clean/formatted |
| `mypy app` (strict) | pass — 35 source files |
| frontend typecheck | pass |
| frontend production build | pass after clearing stale `/app/.next`; the cache otherwise raises `Cannot find module for page: /_not-found` |
| route smoke | **FAIL 5/5 — pre-existing.** `/cases`, `/analytics`, `/ledger`, `/simulator` are not implemented until later frontend tickets; `/` responds 200 but does not contain the old smoke-test label. |

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes (the direct Docker equivalent: `docker compose exec -T backend pytest -q`)
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Decisions and deviations

1. **HNSW uses cosine distance.** `ix_contract_clause_embedding` is an HNSW
   index with `vector_cosine_ops`, `m=16`, and `ef_construction=64`. The model's
   1,536 dimensions remain below pgvector's 2,000-dimension HNSW limit. HNSW is
   chosen over IVFFlat because it works immediately on incremental inserts and
   needs no training/list-count tuning.

2. **The `contract_clause.tsv` index is GIN.** This keeps lexical retrieval
   separate from semantic retrieval so the later reciprocal-rank fusion work can
   query both independently.

3. **`case` is quoted only in raw SQL tests.** `case` is the required table name
   but a PostgreSQL keyword, so integration tests use `"case"`; SQLAlchemy quotes
   the generated DDL automatically.

4. **The vector-plan test uses 2,500 deterministic temporary rows.** With a tiny
   table PostgreSQL correctly prefers a sequential scan, which would make an
   index-use test flaky or misleading. The rows are rolled back after EXPLAIN,
   statistics are refreshed inside the test, and the seeded values keep the test
   deterministic.

5. **TICKET-005's metadata test now checks its owned source subset.** This ticket
   registers the rest of the schema, so TICKET-006 owns the exact full-schema
   assertion. This preserves both ticket contracts instead of treating valid
   later tables as a failure.
