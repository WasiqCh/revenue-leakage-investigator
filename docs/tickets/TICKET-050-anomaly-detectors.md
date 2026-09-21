# TICKET-050 - Anomaly detectors

- **Status:** TODO
- **Phase:** 3 - Deterministic core
- **Effort:** 1.5 day
- **Depends on:** TICKET-016, TICKET-024

## Goal

Add trend, ratio and historical-comparison detectors alongside the existing
rule-based ones.

## What this means

The rule-based detectors from TICKET-018 and TICKET-019 catch problems we already
know the shape of — "contract says 100, billing says 70". These detectors catch
problems nobody wrote a rule for: revenue that suddenly drops, usage that keeps
climbing while billing stays flat, or the same discrepancy reappearing every month.

They do not replace the rules; they run alongside them and catch what the rules
miss.

## Context

Three detector families, all statistical rather than model-based:

- **Trend** — month-over-month revenue change beyond a configured threshold
- **Ratio** — usage-to-billing ratio drifting outside a configured band
- **Historical** — the same discrepancy recurring across consecutive periods

**Every alert must record which detector produced it.** The product principle from
the specification is that the system says "detected by the usage/billing ratio
detector", never "the AI noticed something". An alert with no attribution is a bug.

Deliberately not using Isolation Forest or similar: at 50–100 customers, simple
statistics are more accurate and, critically, explainable to a Finance user.

## Deliverables

- `backend/app/detect/anomaly/trend.py`
- `backend/app/detect/anomaly/ratio.py`
- `backend/app/detect/anomaly/historical.py`
- `backend/tests/unit/test_anomaly_detectors.py`
- `backend/tests/integration/test_anomaly_attribution.py`

## Acceptance criteria

- [ ] a sudden month-over-month revenue drop is detected
- [ ] a usage-to-billing ratio breach is detected
- [ ] a discrepancy recurring across consecutive periods is detected
- [ ] every alert records its `detector_id` — an alert with no attribution fails the test
- [ ] thresholds are read from configuration, not hardcoded
- [ ] zero alerts on 100 clean generated customers

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
