# TICKET-049 - Ingestion layer

- **Status:** TODO
- **Phase:** 2 - Data generation
- **Effort:** 1.5 day
- **Depends on:** TICKET-005, TICKET-006

## Goal

Load business records into the source tables from files and documents, validating
and normalising them on the way in.

## What this means

Everything has to get into the system somehow. This ticket builds the front door:
it takes a CSV of invoices, a JSON export from the CRM, or a folder of contract
documents, checks each one is shaped correctly, converts dates and currencies into
one consistent format, and files it away with a note recording exactly where it
came from.

The important idea is **traceability**. Every row must remember which system and
which record it came from, because later we will be pointing at it as evidence and
saying "this invoice line, from this system, disagrees with this contract clause".
If we lose the origin, the evidence is worthless.

## Context

The architecture shows an INGEST stage between the data sources and the canonical
model. TICKET-033 and TICKET-034 handle CUAD contract documents specifically; this
ticket is the general machinery that everything else uses.

Every ingested row carries `source_system` and `source_id`. Nothing is silently
dropped — a malformed record is logged as an ingestion error and skipped, not
crashed on.

Ingestion is idempotent: loading the same payload twice must not create duplicates,
because `(source_system, source_id)` is a natural key enforced by the schema.

## Deliverables

- `backend/app/ingest/base.py`
- `backend/app/ingest/tabular.py`
- `backend/app/ingest/documents.py`
- `backend/app/ingest/validate.py`
- `backend/app/ingest/normalize.py`
- `backend/tests/unit/test_ingest_validate.py`
- `backend/tests/integration/test_ingest_idempotency.py`

## Acceptance criteria

- [ ] a CSV and a JSON payload both load into the source tables
- [ ] every ingested row carries `source_system` and `source_id`
- [ ] a schema violation raises an error naming the field and the row number
- [ ] timestamps are normalised to UTC and currencies to ISO 4217 codes
- [ ] loading the same payload twice leaves row counts unchanged
- [ ] a malformed record is logged as an ingestion error and skipped, not fatal
- [ ] a test asserts no row exists without a `source_system` value

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
