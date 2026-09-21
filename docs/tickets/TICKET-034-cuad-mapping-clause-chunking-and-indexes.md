# TICKET-034 - CUAD mapping, clause chunking and indexes

- **Status:** TODO
- **Phase:** 6 - RAG and real data
- **Effort:** 1.5 day
- **Depends on:** TICKET-033, TICKET-006

## Goal

Attach real contracts to synthetic customers, split into clauses, embed and index.

## What this means

Give each fake customer a real contract to search. The contract is chopped into individual clauses (not arbitrary blocks) so a citation can point at a precise sentence rather than 'page 4 somewhere'.

## Context

Subset selection is deterministic (sorted hash, no randomness). Every clause gets an embedding and a full-text vector. Real company names must never reach customer rows.

## Deliverables

- `backend/app/rag/chunking.py`
- `backend/app/rag/embeddings.py`
- `backend/app/rag/cuad_mapper.py`
- `backend/tests/integration/test_cuad_mapping.py`

## Acceptance criteria

- [ ] selection is byte-identical across two runs
- [ ] every contract_clause has a non-null embedding and tsv
- [ ] no real company name appears in any customer row (asserted)

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
