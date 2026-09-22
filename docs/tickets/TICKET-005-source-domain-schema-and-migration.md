# TICKET-005 - Source-domain schema and migration

- **Status:** DONE
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

- [x] `backend/app/models/source/` (`__init__.py`, `common.py`, `customer.py`,
      `product.py`, `contract.py`, `subscription.py`, `billing.py`, `usage.py`)
- [x] `one Alembic revision`
      (`alembic/versions/20260922_0030_8071e9ba07f7_source_domain_schema.py`)
- [x] `backend/tests/integration/test_schema_source.py`

## Acceptance criteria

- [x] migration up / down / up succeeds
      (`test_migration_up_down_up_succeeds`)
- [x] a duplicate (source_system, source_id) raises IntegrityError in a test
      (`test_duplicate_source_natural_key_raises_integrity_error`)
- [x] every table has id, created_at, updated_at
      (`test_every_table_has_id_created_at_and_updated_at`, asserted off
      `information_schema`, not off the models)
- [x] a metadata test enumerates the expected source-table subset
      (`test_metadata_and_database_hold_all_expected_source_tables` — asserts
      both `Base.metadata` and the live database contain the 19 source tables;
      TICKET-006 owns the exact full-schema assertion after later tables exist)

## Verification

**Gate G1 — stop here.** Before starting the next ticket, run

```bash
make verify
```

and paste `artifacts/verify-report.md` back. Work does not continue until this
gate is signed off. See [../verification-protocol.md](../verification-protocol.md).

**Gate G1 evidence (2026-09-22).** `make` is not installed in the sandbox this
was built in, so each check the target runs was run by hand through
`docker compose exec`:

| Check | Result |
|---|---|
| migrations up / down / up | pass — `8071e9ba07f7` applies, reverts and re-applies |
| `alembic check` | pass — "No new upgrade operations detected" |
| `alembic current` | `8071e9ba07f7 (head)` |
| ruff check + format | pass — 33 files |
| `mypy app` (strict) | pass — 21 source files |
| pytest | 54 passed, 1 skipped (the docs-parsing config test — `docs/` is not mounted) |
| `npx tsc --noEmit` | pass |
| `npm run build` | pass (after `rm -rf .next`; a stale `.next` cache makes it fail with `Cannot find module for page: /_not-found`) |
| `scripts/smoke_routes.sh` | **FAIL 5/5 — pre-existing.** It expects `/cases`, `/analytics`, `/ledger` and `/simulator`; only `frontend/app/page.tsx` exists. Those pages belong to later frontend tickets. Not caused by this ticket and not fixable here. |

## Definition of done

- [x] every deliverable file exists
- [x] every acceptance criterion above is checked off
- [x] `make test` passes
- [x] no rule in `AGENTS.md` was violated
- [x] status updated to DONE and committed with the co-author trailer

## Deviations and decisions (read before continuing)

1. **No foreign keys from source tables to `customer` or `product`.** Source rows
   carry the **reference string** the external system used (`customer_ref`,
   `product_ref`, `contract_ref`, `invoice_ref`, ...). Deciding which string is
   really which customer is entity resolution's job (TICKET-017); putting a FK
   here would force an ingestion order that does not exist yet and would bake a
   guess into the schema. Foreign keys *are* used between the normalized tables,
   where identity is already resolved: `customer_alias.customer_id`,
   `product_alias.product_id`, `pricing_rule.product_id`.

2. **Every one of the 19 tables gets the `(source_system, source_id)` natural
   key**, including the normalized `customer` and `product`. For those two it
   records the system of record that created the canonical row. This makes
   re-ingestion idempotent uniformly, and it is what makes acceptance criterion
   2 testable on any table.

3. **`usage_snapshot` and `fx_rate` carry a second unique constraint** for the
   business key `docs/data-model.md` specifies —
   `(customer_ref, product_ref, metric, period_start)` and
   `(base_currency, quote_currency, as_of_date)`. Declaring `__table_args__` in a
   class replaces the mixin's, so both constraints are listed explicitly in both.

4. **The embedding width is hard-coded to 1536**, not read from
   `Settings.embedding_dimensions`. A column's width is part of the schema, so it
   must not change with an environment variable — two databases would then
   disagree about the same migration. `test_embedding_column_matches_the_configured_width`
   asserts the constant still matches the setting.

5. **The pgvector and GIN indexes are NOT created here.** `contract_clause`
   gains `embedding vector(1536)` and `tsv tsvector` now, but TICKET-006 owns
   both indexes and the EXPLAIN that proves they are used. Creating them early
   would leave that acceptance criterion with nothing to prove.

6. **`alembic/env.py` was extended with a `Vector` and a `TSVECTOR` render
   rule.** Autogenerate emitted `pgvector.sqlalchemy.vector.VECTOR(dim=1536)`
   with no import, which crashes on upgrade — the same class of bug the
   `MoneyType` rule fixed in TICKET-004.

7. **32 lookup indexes were added** (customer/product/contract/subscription/
   invoice references, service-period dates, SCD-2 `is_current`), because the
   ticket's goal asks for "indexes and natural-key uniqueness" and every detector
   later filters on those columns. The natural-key constraints add their own
   indexes on top.

8. **`contract_term` is modelled as SRC/DERIV** exactly as the data model marks
   it, with `extraction_method` recording whether a rule, the model or a human
   produced the value.

9. **`subscription_line` is SCD-2**: a change closes the previous row by setting
   `valid_to` and opens a new one. `is_current` is the shortcut for "the row that
   applies now". No partial unique index on `is_current` yet — if TICKET-013
   needs one, add it there.

10. **Follow-up commit on this branch clears the tier-1 gate for 001–005.**
    `scripts/verify_ticket.py` was failing every ticket with SEV2 "environment
    read outside config.py": tests were calling `os.environ.get("DATABASE_URL")`
    to decide whether to skip. Added `Settings.settings_or_none()` to
    `app/config.py` — the one module allowed to look at the environment — and
    routed all seven call sites through it, including two in files owned by
    earlier tickets (`tests/test_database_stack.py`, `tests/test_offline_env.py`).
    The fix is committed here because the gate verdict is repo-wide: leaving it
    in an earlier branch would keep every later ticket red. Also fixed a
    duplicated "Deliverables" block I had accidentally left in TICKET-004, which
    was making the verifier look for `alembic.ini` at the repo root.

11. **The source-schema metadata test now asserts its 19-table subset, not the
    entire application schema.** TICKET-006 correctly registers 21 additional
    derived/case/ops tables. Keeping TICKET-005's test exact would make a later,
    valid schema expansion look like a regression. TICKET-006 adds the one
    exact full-schema test instead.
