# TICKET-048 - Managed-RAG comparison baseline (Cloudflare AI Search)

- **Status:** TODO
- **Phase:** 9 - Evaluation
- **Effort:** 1.0 day
- **Depends on:** TICKET-035, TICKET-045

## Goal

Optionally benchmark our own retrieval against Cloudflare AI Search and record the result.

## What this means

A 'how do we know ours is any good?' check. We point the same questions at a paid managed search service and compare. This is for measurement only - the product itself keeps using the pipeline we built.

## Context

Deliberately optional and skipped when credentials are absent. Exists to demonstrate engineering judgement: we considered the managed option, measured it, and documented why we kept our own. See docs/adr/ADR-009-cloudflare-ai-search.md.

## Deliverables

- `backend/app/eval/suites/managed_baseline.py`
- `docs/adr/ADR-009-cloudflare-ai-search.md`

## Acceptance criteria

- [ ] with no credentials configured the suite skips cleanly and still passes
- [ ] the same frozen 30-clause set is used for both sides of the comparison
- [ ] results are recorded with a note that no managed service is used in the product path
- [ ] no application code path depends on this suite

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
