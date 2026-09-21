# TICKET-035 - Hybrid retrieval with reciprocal rank fusion

- **Status:** TODO
- **Phase:** 6 - RAG and real data
- **Effort:** 1.0 day
- **Depends on:** TICKET-034

## Goal

Combine semantic vector search with keyword search and fuse the rankings.

## What this means

Search contracts two ways at once - by meaning and by exact words - then merge the two result lists. Meaning alone misses exact terms; keywords alone miss paraphrases. Together they are much better than either.

## Context

pgvector semantic search plus Postgres full-text search, combined with reciprocal rank fusion.

## Deliverables

- `backend/app/rag/retrieval.py`
- `backend/tests/integration/test_retrieval.py`

## Acceptance criteria

- [ ] a query with a distinctive clause phrase returns the correct clause in the top 3
- [ ] both the lexical-only and semantic-only paths are exercised by tests
- [ ] RRF ordering is deterministic

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
