# TICKET-005 - Source-domain schema and migration

- **Status:** TODO
- **Phase:** 1 - Schema
- **Effort:** 1.5 day
- **Depends on:** TICKET-004

## Goal

All source and normalized tables with indexes and natural-key uniqueness.

## What this means

Create the tables that hold the raw business records: customers, contracts, products, invoices, usage and so on - exactly as the outside systems report them.

## Context

Tables: customer, customer_alias, product, product_alias, pricing_rule, fx_rate, contract, contract_clause, contract_term, amendment, amendment_term, subscription, subscription_line, implementation, usage_snapshot, invoice, invoice_line, credit_memo, crm_opportunity.

## Deliverables

- `backend/app/models/source/`
- `one Alembic revision`
- `backend/tests/integration/test_schema_source.py`

## Acceptance criteria

- [ ] migration up / down / up succeeds
- [ ] a duplicate (source_system, source_id) raises IntegrityError in a test
- [ ] every table has id, created_at, updated_at
- [ ] a metadata test enumerates the expected table set exactly

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
