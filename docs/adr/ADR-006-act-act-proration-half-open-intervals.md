# ADR-006: Half-open billing periods and ACT/ACT proration

**Status:** Accepted — 2026-09-21

## What this means

A **billing period** is the stretch of time an invoice covers, normally a month. We define every period as a **half-open interval**, written `[start, end)`: it includes the start date and excludes the end date, so January is 1 January up to but not including 1 February. The brackets are the point — with half-open intervals, consecutive periods tile the calendar perfectly, with no day counted twice and none missed. **Proration** is what you charge when someone starts or stops partway through a period, and it needs a rule for counting days. Ours is **ACT/ACT**: the actual number of calendar days being charged, divided by the actual number of days in that period. Starting on 20 January means paying for the 12 actual days from 20 to 31 January out of January's actual 31. One further wrinkle: contracts often anchor on the 31st and February has no 31st, so when the anchor day does not exist we clamp backward to that month's last day, and the *next* period resumes on the anchor day rather than staying on the clamped day.

## Context

Billing date maths is where revenue systems quietly lose and gain money, and it is the hardest part of this product. Three traps forced the decision. The double-count trap: an inclusive range means the day that closes one period also opens the next, so monthly totals depend on how boundaries were chunked. The proration trap: there is no universal answer to "how much is 12 days of a month worth" — 30/360 assumes every month has 30 days and gives tidy numbers, while ACT/ACT uses the real calendar and matches what a customer can count. The anchor trap: a contract starting 31 January has no obvious February date, and clamping to 28, rolling to 1 March, or skipping to 31 March give three different revenues — while a naive implementation drifts forever, because every later period inherits the clamped day. Rounding is the fourth trap: rounding intermediates accumulates error across a year.

## Decision

**Billing periods are half-open intervals `[start, end)`. Proration is ACT/ACT over actual calendar days. An anchor day of 29–31 clamps backward to the month's last day, and the following period resumes on the anchor day — the clamp is per-boundary, not sticky. Monetary results quantise to 2 decimal places with `ROUND_HALF_UP`.**

- Period enumeration, day counting and proration live in `backend/app/billing/`, take an explicit `as_of_date`, and never call `datetime.now()`.
- The clamp is recomputed from the contract's stored anchor day each time, so the period after a clamped February returns to the 31st.
- Quantisation happens once, where a monetary value is produced for storage or display; intermediate arithmetic keeps full `Decimal` precision.
- A Hypothesis property test asserts that periods generated over any span tile the calendar with no gaps and no overlaps, and that the sum of prorated parts equals the prorated whole.
- `docs/billing-periods.md` documents the rules with worked examples.

## Alternatives considered

- **30/360 day count.** Rejected. Standard in lending and rounder, but it is not what a SaaS customer expects to see on an invoice, it is hardest to defend to a customer who counts the days themselves, and it produces a "30 February". Accepted trade-off: ACT/ACT gives less tidy daily rates, and a February day is genuinely worth more than a March day.
- **ACT/365 fixed.** Rejected. Simple and consistent per period, but twelve monthly charges no longer sum to the annual contract value, which is the first thing a Finance reviewer checks.
- **Inclusive `[start, end]` intervals.** Rejected. It double-counts boundary days and makes totals depend on how periods were chunked, which breaks reconciliation entirely.
- **Rolling the anchor forward to the first of the next month.** Rejected. It shortens the period and permanently changes the billing day, which customers dispute.
- **Sticky clamping (31 Jan → 28 Feb → 28 Mar → …).** Rejected. The tempting simple implementation, and it silently migrates a month-end contract to the 28th forever.
- **Rounding at every intermediate step.** Rejected. It accumulates drift; we round once, at the output boundary.
- **Floating point.** Rejected without discussion — see [ADR-001](ADR-001-deterministic-money-no-llm-math.md).

## Consequences

**Easier.** Periods tile the calendar exactly, so re-running detection over any range gives identical results and a monthly total is simply the sum of its periods. Proration is explainable because a reviewer can count the days. Money ties out across the year with no rounding drift, month-end contracts stay on month-end, and every rule is provable with a property test rather than argued about.

**Harder.** Day counting is date-aware, so periods are not interchangeable and cannot be treated as uniform buckets; cache keys and aggregates must key on the real boundaries. Explaining ACT/ACT to a customer who expects 30/360 needs a documented example, which is why `docs/billing-periods.md` exists.

**Negative.** Some real contracts specify 30/360 or a fixed 365-day year. We do not support those, so such a customer cannot be modelled faithfully — the system computes ACT/ACT and disagrees with their actual invoice. We treat this as a known scope limit rather than a bug, and it is one reason the product proposes corrections for human review instead of applying them.

## How to reverse it

Changing the day-count convention means changing one module and re-deriving every prorated amount, so stored values must be treated as derived rather than as records. Changing the interval convention is more invasive: every period comparison, boundary predicate and property test would need review, because a half-open assumption is threaded through the billing and reconciliation code.
