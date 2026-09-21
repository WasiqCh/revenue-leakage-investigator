# TICKET-011 - Usage, invoice and billing generators with injected drift

- **Status:** TODO
- **Phase:** 2 - Data generation
- **Effort:** 1.5 day
- **Depends on:** TICKET-010

## Goal

Generate operational records, then inject the specific drift the scenario calls for.

## What this means

Create the invoices and usage logs, then deliberately break them in the exact way the recipe says - so billing says 70 seats while everything else says 100.

## Context

Produces usage snapshots, invoices, invoice lines, credit memos, implementation records, CRM opportunities and pricing rules, then applies the drift.

## Deliverables

- `backend/app/generate/drift.py`
- `backend/tests/integration/test_generated_data.py`

## Acceptance criteria

- [ ] for each leak type the generated database state reproduces the intended discrepancy exactly
- [ ] a test recomputes the expected difference from raw rows and matches the manifest
- [ ] exception scenarios produce an approved_exception row and no discrepancy

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
