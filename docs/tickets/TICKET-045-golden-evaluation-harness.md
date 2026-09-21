# TICKET-045 - Golden evaluation harness

- **Status:** TODO
- **Phase:** 9 - Evaluation
- **Effort:** 2.0 days
- **Depends on:** TICKET-019, TICKET-025, TICKET-026

## Goal

Score detection precision and recall, exception classification and confidence calibration.

## What this means

The report card. Because the fake data was generated from recipes, we know every right answer - so we can measure exactly how often the system is right, how often it cries wolf, and whether its confidence scores actually mean anything.

## Context

Writes metrics to eval_run and eval_result, reproducible from git_sha plus dataset_version.

## Deliverables

- `backend/app/eval/harness.py`
- `backend/app/eval/suites/detection.py`
- `backend/app/eval/suites/exceptions.py`
- `backend/app/eval/suites/calibration.py`
- `backend/tests/integration/test_eval_harness.py`

## Acceptance criteria

- [ ] on the seeded golden set, detection recall is at least 0.95
- [ ] detection precision is at least 0.90
- [ ] every legitimate exception is classified as VALID_EXCEPTION with zero false leakage cases
- [ ] metrics are written to eval_run and eval_result and are reproducible

## Verification

**Gate G9 — stop here.** Before starting the next ticket, run

```bash
make verify
```

and paste `artifacts/verify-report.md` back. Work does not continue until this
gate is signed off. See [../verification-protocol.md](../verification-protocol.md).

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
