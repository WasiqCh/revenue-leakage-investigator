# TICKET-012 - Ground-truth manifests, golden labels and seed command

- **Status:** TODO
- **Phase:** 2 - Data generation
- **Effort:** 1.0 day
- **Depends on:** TICKET-011

## Goal

Emit per-customer answer keys, load them as golden labels, expose the seed CLI.

## What this means

Alongside the fake data, write down the answer sheet: which customers have real leakage, how much, and which ones are fine. Later we grade the system against it.

## Context

Manifests are emitted per customer and loaded into golden_label. `make seed` and `python -m app.cli seed --seed N --customers M` are the entry points.

## Deliverables

- `backend/app/generate/manifest.py`
- `backend/app/cli.py (seed command)`
- `fixtures/golden/`
- `backend/tests/integration/test_seed_determinism.py`

## Acceptance criteria

- [ ] running seed twice with the same seed leaves row counts unchanged and manifest bytes identical
- [ ] golden_label row count equals the number of expected findings
- [ ] `make seed` is idempotent

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
