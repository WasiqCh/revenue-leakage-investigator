# TICKET-033 - CUAD downloader, cache, offline fixture and licence notice

- **Status:** TODO
- **Phase:** 6 - RAG and real data
- **Effort:** 1.5 day
- **Depends on:** TICKET-003

## Goal

Fetch the public CUAD contract dataset, cache it safely, and record its licence.

## What this means

Bring in real contracts written by real lawyers so we are testing against genuine messy legal prose rather than text we invented. The files are cached outside the repo and never committed, because the dataset licence is not clearly published.

## Context

Verifies the archive hash against the known md5. Supports CUAD_OFFLINE=1 via a small committed fixture so tests never need the network. Writes THIRD_PARTY_NOTICES.md.

## Deliverables

- `scripts/fetch_cuad.py`
- `backend/app/rag/cuad_adapter.py`
- `fixtures/cuad_sample.json`
- `THIRD_PARTY_NOTICES.md`

## Acceptance criteria

- [ ] CUAD_OFFLINE=1 succeeds with zero network and returns 3 contracts
- [ ] a corrupted cache (bad hash) triggers a re-download
- [ ] contract text is never written into the repo tree
- [ ] the licence string is recorded, and the script fails loudly if it cannot be determined

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
