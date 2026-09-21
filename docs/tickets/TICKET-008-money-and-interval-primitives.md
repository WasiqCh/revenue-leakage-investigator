# TICKET-008 - Money and interval primitives

- **Status:** TODO
- **Phase:** 1 - Schema
- **Effort:** 1.0 day
- **Depends on:** TICKET-004

## Goal

Currency-aware Decimal money type, FX helpers, and half-open date interval algebra.

## What this means

The maths building blocks. Money is stored as exact decimals (never floating point, because 0.1 + 0.2 is not 0.3 in floats and that error compounds in financial reports). Date ranges are treated as start-inclusive, end-exclusive so periods never overlap or leave gaps.

## Context

DecimalMoney with add / multiply / quantize using ROUND_HALF_UP and per-currency minor units. Interval operations: intersect, subtract, length, merge.

## Deliverables

- `backend/app/money/decimal_money.py`
- `backend/app/money/interval.py`
- `backend/app/money/fx.py`
- `backend/tests/unit/test_money.py`
- `backend/tests/property/test_interval.py`

## Acceptance criteria

- [ ] Hypothesis proves interval length is additive under partitioning
- [ ] Hypothesis proves subtract never yields a negative length
- [ ] a test asserts Decimal never degrades to float
- [ ] FX walk-back returns the nearest prior business day and raises when none exists

## Verification

**Checked individually**, not only at the next gate, because:

- Everything downstream depends on exact money arithmetic.

Run `make verify` and share `artifacts/verify-report.md` as soon as this ticket
is complete.

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
