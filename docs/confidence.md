# Confidence

## What this means

If you ask a language model *"how confident are you in this answer?"*, it will say
something like **"I am 94% confident."** That number is meaningless. It is not
measured against anything, it is not stable between runs, and it is highest
exactly when the model is making things up.

So confidence here is not the model's opinion. It is **computed by code**, from
factors that can each be measured against the database, using a published
formula with published weights. The AI contributes exactly **one** input out of
eight: `contract_clarity`, which asks whether the contract is explicit, implied,
ambiguous or silent about the thing being billed. Everything else is arithmetic.

The practical consequence: two people looking at the same case see the same
confidence score and can see **why** it is that number. A score is explainable,
reproducible and testable — none of which is true of a model self-reporting.

Implementation lives in `backend/app/cases/confidence.py`. It is the **only**
writer of `case.confidence_score` (enforced by a single-writer helper plus a test
that greps for other writers).

## Split of responsibility

| Who | Produces |
|---|---|
| **LLM** | The enum `contract_clarity ∈ {explicit, implied, ambiguous, silent}`, plus prose (hypothesis, root cause, narrative, draft proposed correction). |
| **Code** | Every number: all eight factors, the weighted sum, the gates, the score, the band. |

The LLM may never emit a currency amount, a seat count, a date, a quantity or a
percentage that ends up stored or displayed.

## The eight factors

Each factor returns a `Decimal` in `[0, 1]`. Weights sum to exactly `1.00`.

| Factor | Weight | How it is computed (all code) |
|---|---|---|
| `evidence_completeness` | 0.25 | `present_required_types / required_types(leak_type)`. "Present" means an `evidence` row with a non-null `source_pk` that the Verifier successfully re-fetched. |
| `source_agreement` | 0.20 | Fraction of cross-source facts that agree (contract vs CRM vs billing) on price, quantity and period. Disagreements reduce it proportionally. |
| `deterministic_certainty` | 0.15 | Intrinsic to the check: exact numeric difference = 1.0; date-boundary difference = 0.9; entity-resolution-dependent = 0.7; usage-derived = 0.8. Table lives in `detect/checks/registry.py`. |
| `contract_clarity` | 0.10 | `explicit` = 1.0, `implied` = 0.75, `ambiguous` = 0.35, `silent` = 0.0. **The only LLM-sourced input.** |
| `exception_absence` | 0.10 | 1.0 if no `approved_exception` overlaps the period; 0.0 if one does (which routes the case to `VALID_EXCEPTION` regardless). |
| `data_freshness` | 0.08 | `clamp(1 − (as_of − newest_evidence_source_ts) / 90 days, 0, 1)`. |
| `historical_precedent` | 0.07 | Laplace-smoothed (i.e. add one success and one failure so small samples cannot produce 0 or 1) approval rate for this `leak_type` from `case_outcome`: `(approvals + 1) / (approvals + rejections + 2)`. |
| `amount_materiality` | 0.05 | `min(1, log1p(amount / MATERIALITY_THRESHOLD) / log1p(10))`. Larger amounts score higher, with diminishing returns. |

The weighted sum:

```
raw = 100 × Σ(weight_i × factor_i)
```

## Hard gates

Gates are applied **after** the weighted sum. They exist because some conditions
are safety-critical and must not be tradeable against nice-to-have factors — a
case with beautiful evidence but a failed arithmetic check is not 96% confident,
it is untrustworthy.

| # | Gate | Effect |
|---|---|---|
| 1 | Verifier failed any numeric claim | `score = min(raw, 60)` and force `NEEDS_REVIEW` |
| 2 | Any required evidence type missing | `score = min(raw, 74)` — can never be "high" |
| 3 | Conflicting cross-source evidence | `status = CONFLICTING_EVIDENCE`, `score = min(raw, 65)` |
| 4 | Overlapping approved exception | `status = VALID_EXCEPTION`; the score is stored for calibration but unused |
| 5 | `deterministic_certainty == 1.0` **and** evidence complete **and** no exception | `score = max(raw, 85)` — a floor |

**Gates can only lower or floor a score; they can never raise it.** Gate 5 is the
only floor, and it applies solely to the fully-clean case. There is no path by
which a gate turns a weak case into a strong one.

## Bands

Bands are computed on the score **rounded to 2 decimal places**, so the boundary
behaves identically every time:

| Band | Condition | Meaning |
|---|---|---|
| `high` | `score > 90` | Straightforward case, ready for a fast review |
| `medium` | `75 ≤ score ≤ 90` | Solid but with something imperfect about it |
| `manual` | `score < 75` | A human must look properly; the system is not claiming an answer |

Note that gate 2 caps at 74, which is deliberately just below the `medium` floor:
a case missing required evidence can never present itself as more than manual.

## Worked example

A `SEAT_UNDERBILLING` case. Contract says 100 seats, CRM agrees, billing invoiced
70. The newest evidence source timestamp is 15 days before `as_of_date`. This
`leak_type` has previously been approved 18 times and rejected twice. The amount
is roughly 4.4× the materiality threshold.

**Step 1 — factors.**

| Factor | Value | Weight | Contribution |
|---|---|---|---|
| `evidence_completeness` | 1.0000 | 0.25 | 0.250000 |
| `source_agreement` | 1.0000 | 0.20 | 0.200000 |
| `deterministic_certainty` | 1.0000 | 0.15 | 0.150000 |
| `contract_clarity` (explicit) | 1.0000 | 0.10 | 0.100000 |
| `exception_absence` | 1.0000 | 0.10 | 0.100000 |
| `data_freshness` | 0.8333 | 0.08 | 0.066667 |
| `historical_precedent` | 0.8636 | 0.07 | 0.060455 |
| `amount_materiality` | 0.7000 | 0.05 | 0.035000 |
| **Total** | | **1.00** | **0.962121** |

`raw = 100 × 0.962121 = 96.2121`, which rounds to **96.21**.

**Step 2 — gates.**

- Gate 5 applies: `deterministic_certainty` is 1.0, evidence is complete, no
  exception overlaps. Floor of 85 → `max(96.21, 85) = 96.21`. No change.
- Band: `96.21 > 90` → **`high`**.

Now suppose the same case, but the Verifier finds that one number in the agent's
report — the seat count of 70 — cannot be re-fetched from any recorded tool
result. The agent asserted it without evidence.

- Gate 1 applies: `score = min(96.21, 60) = 60`, and the case is forced to
  `NEEDS_REVIEW`.
- Band: `60 < 75` → **`manual`**.

The case does not disappear and the finding is not discarded. It goes to a human
with the report intact, marked as unverified. That is the point: the gate changes
who decides, not whether the case is looked at.

A third variant, for contrast: identical, but one required evidence type is
missing. Gate 2 → `min(96.21, 74) = 74` → band `manual`. Just below the line,
by design.

## Tests this document requires

- **Determinism** (property test): identical inputs always produce an identical
  score.
- **Monotonicity**: adding a required evidence row never lowers the score.
- **Gate caps**: a verifier failure caps at 60; a missing required evidence type
  caps at 74; a clean deterministic case floors at 85.
- **Band boundaries**: `75.00` and `90.00` behave exactly as specified.
- **Calibration** (on the golden set): cases in the `high` band are confirmed by
  humans at precision ≥ 0.9.
