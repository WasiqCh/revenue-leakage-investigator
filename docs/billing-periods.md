# Billing periods and proration

## What this means

Billing periods sound like the trivial part of the system. They are in fact the single
most common source of wrong answers in revenue software, and the wrong answers are
expensive in both directions: a date rule off by a few days either **invents** money
that was never owed or **hides** money that was.

Here is the example that makes it real. A deal is signed on **15 March**. The contract
says *"billing starts the first full billing period following the Effective Date"*, so
March is deliberately **not billed** — it is a partial month and the contract says we
skip it. April is billed in full.

Without that rule, March looks like a month where a paying customer generated no
invoice. A naive system flags it as leakage, Finance chases a customer for money that
was never owed, and the customer — who is right — loses confidence in the whole
product. Confusing a **stub period** with a **bug** either invents money or hides
money. Every rule below exists to make that impossible. This is the specification for
`backend/app/billing/periods.py` and `backend/app/billing/proration.py`.

## Period definition

A billing period is a **half-open interval** — it includes the start date and excludes
the end date, written `[start, end)`. A period from 1 April to 1 May contains every day
in April and no day of May. Half-open intervals make periods tile perfectly: no day
belongs to two periods, and no day falls between two.

`period_days = (end - start).days` — whole calendar days, an integer.

A period covers `billing_frequency` months (monthly, quarterly or annual). The
`billing_period` table is materialised — rows are physically stored, not computed on
the fly — so every period has a stable identity that evidence and audit records can
point at. Rows are upserted on `unique(subscription_id, period_index)`, where
`period_index` is a 0-based integer counted from the subscription's first billable
period. That key is why indices stay stable across re-runs.

### Anchor modes

The **anchor** is the rule that decides where period boundaries fall.

| Anchor | Boundary rule | Anchor day |
|---|---|---|
| `CALENDAR_MONTH` | Periods are `[1st of month, 1st of next month)`. | 1 |
| `ANNIVERSARY` | Periods start on `billing_anchor_day` of the subscription start month, then step by `billing_frequency` months. | `subscription.billing_anchor_day` |
| `CONTRACT_EFFECTIVE_DAY` | As anniversary, but anchored on `contract.effective_date.day`. | `contract.effective_date.day` |

`ANNIVERSARY` from `2024-03-15`, monthly: `[2024-03-15, 2024-04-15)`,
`[2024-04-15, 2024-05-15)`, `[2024-05-15, 2024-06-15)`, and so on.

### Backward clamping (anchor days 29-31)

Not every month has a 31st. The rule is **clamp backward, do not roll forward**: if
`billing_anchor_day` is greater than the number of days in the target month, the
boundary is pulled back to the **last day of that month**.

Clamping is **per-boundary, not sticky** — the part implementations get wrong. The
anchor day is not modified; it is re-evaluated against each month independently, so the
period after a clamped one returns to the anchor day. With anchor day 31:

```
[2024-01-31, 2024-02-29)      # February 2024 clamps to its last day (leap year)
[2024-02-29, 2024-03-31)      # resumes on the 31st, not the 29th
[2024-03-31, 2024-04-30)      # April clamps to 30
[2024-04-30, 2024-05-31)      # resumes on the 31st
```

A "roll forward" rule would turn 31 January + one month into 2 or 3 March and drift
forever. Clamping keeps the boundary where the customer expects it.

## Which date starts billing

Billing does not start on the contract signature date, and it does not start when the
customer first logs in. It starts on the **billable start**, computed deterministically:

```
billable_start = max(contract.effective_date,
                     subscription.start_date,
                     coalesce(implementation.actual_activation_date,
                              implementation.go_live_date))
```

The `max` is deliberate: the latest of the three. If a contract is effective 1 April
but the customer is only activated on 20 April, billing starts 20 April — we do not
charge for a product that was not running.

### Commencement overrides

A contract may contain a `contract_term` with `term_type = 'billing_commencement'`.
This overrides the computed start and is the literal source of the "first full billing
period" language in the contract:

| Override value | Meaning | Is the partial interval billed? |
|---|---|---|
| `IMMEDIATE` | Use `billable_start` exactly as computed. | Yes — prorated |
| `FIRST_FULL_PERIOD` | The first period `P` in the anchored sequence with `P.start >= billable_start`. Any partial interval before `P` is a **stub** and is **not billed** (zero charge). | No |
| `NEXT_PERIOD_START` | The start of the period that begins strictly after `billable_start`. | Yes — prorated as a stub |

`FIRST_FULL_PERIOD` is the literal meaning of *"the first full billing period following
the Effective Date"*. The preceding partial interval is a stub with a zero charge — not
a missing invoice, and never a leakage finding.

## Proration

The convention is **ACT/ACT** — actual days over actual days. A part-month charge is
the fraction of the period actually covered, using real calendar days. `30/360` and
`ACT/365` are **explicitly rejected**: monthly SaaS billing is calendar-day based, and
a 31-day month is not a 30-day month.

For a coverage interval `C = [c_start, c_end)` intersecting a period
`P = [p_start, p_end)`:

```
billed_days = (min(c_end, p_end) - max(c_start, p_start)).days
period_days = (p_end - p_start).days
factor      = Decimal(billed_days) / Decimal(period_days)   # held at 4 dp internally
line_amount = quantize(unit_price * quantity * factor, 2, ROUND_HALF_UP)
```

Notes that matter:

- **Stub periods use the same formula.** There is no special case; a stub is just a
  coverage interval that happens to be short.
- **Mid-period quantity changes** (seat adds, tier crossings) split the period at each
  change date into sub-intervals `[d0,d1), [d1,d2), …`, prorate each sub-interval
  against the quantity effective during it, and sum. This is what makes
  `SEAT_UNDERBILLING` arithmetic unambiguous when seats change mid-month.
- **Annual and quarterly prepay** use the same ACT/ACT rule over the longer period.
  There is no separate annual convention.
- **Rounding** is `Decimal` throughout, quantised to 2 dp at line level and again at
  invoice and period aggregation, so expected and actual compare like for like.
  Currency minor units come from the currency table (2 generally, 0 for JPY).

## Period-boundary mismatches, converted to dollars

Detection compares the **expected** service coverage `E = [exp_start, exp_end)` from the
rules above against the **actual** coverage `A = [act_start, act_end)` read from
`invoice_line.service_period_start/end`. Interval algebra lives in
`backend/app/money/interval.py`, in whole integer days, and `daily_rate` is the ACT/ACT
day rate:

```
daily_rate = expected_period_amount / period_days
```

| Situation | Condition | Finding | Dollar impact |
|---|---|---|---|
| Leading gap | `act_start > exp_start` | under-billed | `daily_rate * (act_start − exp_start)` |
| Trailing gap | `act_end < exp_end` | under-billed | `daily_rate * (exp_end − act_end)` |
| Billed early | `act_start < exp_start` | over-billed | `daily_rate * (exp_start − act_start)` (negative leakage) |
| Short period | `act_end > exp_end` | over-billed | `daily_rate * (act_end − exp_end)` |
| Double coverage | two lines cover the same day | double-billing | `sum(daily_rate * overlap_days)` |

**Over-billing is never netted.** A negative delta is emitted as a separate
`OVERBILLING` finding, through the same case machinery, carrying an explicit sign. It
does not reduce the leakage total of the under-billing case: netting would hide two
facts behind one number, and both matter — one is money to collect, the other is money
to credit.

### Worked example

Contract effective `2024-03-15`. Monthly, calendar-month anchor, `FIRST_FULL_PERIOD`,
price **$12,000/month**.

`billable_start = 2024-03-15`. The first full period is `[2024-04-01, 2024-05-01)` →
30 days. The March stub `[2024-03-15, 2024-04-01)` = 17 days is **not billed**. The
actual invoice line covers service period `[2024-04-01, 2024-04-16)` for **$6,000**.

Comparing `exp = [2024-04-01, 2024-05-01)` with `act = [2024-04-01, 2024-04-16)`: the
start matches and the end is 15 days short → **trailing gap**.
`daily_rate = 12000 / 30 = 400`, so leakage `= 400 × 15 =` **$6,000**.

The March stub contributes nothing, and it is correct that it contributes nothing.

### Tolerance

A difference is only a mismatch if it clears the tolerance:

```
abs(delta) > max(1.00, 0.005 * abs(expected))
```

In plain terms: either more than one unit of currency, or more than half a percent of
what was expected — whichever is larger. This absorbs sub-cent rounding without hiding
a real error. The thresholds are configurable (`MONEY_TOLERANCE_ABS`,
`MONEY_TOLERANCE_PCT`) and are hashed into `reconciliation_run.config_hash`, so a run
is reproducible from its settings.

## Edge cases

| Case | Expected behaviour |
|---|---|
| Anchor day 31, target month has 30 days | Boundary clamps to the 30th; next period resumes on the 31st |
| Anchor day 31, February | Clamps to Feb 28, or Feb 29 in a leap year; next period resumes on the 31st |
| Anchor day 29, non-leap February | Clamps to Feb 28; next period resumes on the 29th |
| Partial month before `FIRST_FULL_PERIOD` | Stub with zero charge. Never a leakage finding |
| `NEXT_PERIOD_START` with a partial interval | Partial interval is billed as a prorated stub |
| `IMMEDIATE` with a mid-month start | First period is prorated ACT/ACT, no stub |
| Mid-period seat change | Period split at the change date; each sub-interval prorated at its own quantity, then summed |
| Annual prepay covering a mid-term change | Same ACT/ACT rule applied over the longer period |
| Invoice covers days *before* the expected start | `OVERBILLING` finding, negative amount, separate case |
| Two invoice lines cover the same day | Double-coverage finding, amounts summed across overlaps |
| Delta exactly at tolerance | **Pass** — the comparison is strictly greater-than |
| Currency with 0 minor units (JPY) | Quantise to 0 dp, taken from the currency table |
| Re-running detection | Identical periods, identical indices, zero new cases |
