# TICKET-006 - Derived, case and ops schema and migration

- **Status:** TODO
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

- `backend/app/models/derived/`
- `backend/app/models/case/`
- `backend/app/models/ops/`
- `one Alembic revision`
- `backend/tests/integration/test_schema_derived.py`

## Acceptance criteria

- [ ] migration up / down / up succeeds
- [ ] case.case_key is unique
- [ ] reconciliation_result is unique on (run_id, customer, line, period, check_code)
- [ ] EXPLAIN on a vector similarity query uses the vector index

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
