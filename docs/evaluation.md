# Evaluation

## What this means

A system like this is only worth anything if you can **prove** it works. "It
looked right in the demo" is not proof. Proof means grading the system against an
**answer key** — a list of the right answers — and reporting the score.

Normally the answer key is the expensive part. A human has to read hundreds of
real cases and mark up which ones are genuinely leaking money. That is slow,
error-prone and never finished.

We get the answer key **for free**, and this is the neatest trick in the project.
The test data is not found, it is *generated*. We write a scenario template that
says *"this customer is under-billed by 30 seats for five months"* and then we
generate a company that has exactly that defect in it. Because we built the
defect, we know the right answer by construction. Ground truth is a by-product of
generation, not a labelling project.

The one exception is real legal prose. Real contracts from the CUAD dataset come
with lawyer-made clause labels, which gives a second free answer key for the
clause-reading part of the system.

## The golden dataset

The golden dataset is built by construction from **scenario templates**:

- 50–100 synthetic customers, 12 months of history.
- The **10 deliberate leakage patterns**, each generated from a typed
  `ScenarioSpec` that declares which systems drift, the expected evidence types
  and the expected root cause.
- A set of **exception-only** scenarios — approved discount, free pilot, grace
  period, grandfathered expired discount — which look exactly like leakage and
  are not.
- Clean customers, whose expected finding count is zero. These are how
  false-positive rate is measured; a detector that fires on everything scores
  perfectly on recall and is worthless.

Each customer emits a **manifest**, loaded into the `golden_label` table:

| Field | Meaning |
|---|---|
| `leak_type` | Which of the ten defects this is |
| `expected_detected` | Should the system find it at all |
| `affected_periods` | Which billing periods should be attached |
| `expected_amount` | The correct money impact |
| `expected_annualized` | The correct annualised figure, including which branch was taken |
| `expected_exception_type` | If this is legitimate, which exception it is |
| `expected_confidence_band` | `high` / `medium` / `manual` |
| `expected_evidence_types` | Which evidence types must be present |

Generation is **seeded and deterministic**: the same seed produces byte-identical
manifests. That is what makes a score comparable between runs.

### Labelled categories

Every scenario falls into exactly one of four categories, and the system's job is
to land in the right one:

| Category | What it is | Correct system behaviour |
|---|---|---|
| **True leakage** | Money owed and not collected | Detect it, quantify it, propose a correction |
| **Legitimate exception** | An approved discount, pilot, grace period or grandfathered rate | Classify as `VALID_EXCEPTION`, propose nothing, ideally with zero LLM calls |
| **Ambiguous** | Genuinely cannot be determined from the data | Say so — `NEEDS_REVIEW` or `CONFLICTING_EVIDENCE`. Guessing is the failure |
| **False positive** | Clean, and the system flagged it anyway | Not flag it. If flagged, the human `REJECTED` outcome records `false_positive` |

The ambiguous category is the one most systems get wrong. A system that guesses
confidently on ambiguous data produces exactly the noise that makes Finance stop
trusting the queue — which is why "correctly abstaining" is a scored outcome, not
a non-answer.

## Metrics and targets

These are the thresholds asserted in CI. `make eval` fails if any is missed.

| Metric | Target | How measured |
|---|---|---|
| Detection recall | ≥ 0.95 | Fraction of true-leakage scenarios detected, against `golden_label` |
| Detection precision | ≥ 0.90 | Of the cases raised, fraction that are genuine |
| Exception classification | ≥ 8 of 10 | Legitimate-exception scenarios classified `VALID_EXCEPTION` |
| Money accuracy | 100% | Unit tests plus Hypothesis property tests on every money function |
| Citation grounding | ≥ 90% | Citations that resolve to a real `evidence` row with a real `source_pk` |
| Confidence calibration | ≥ 85% | Cases scored > 90 that humans confirm |
| Idempotency | zero duplicates | Running detection twice creates no new cases |
| Guardrail | proven | A test proves no code path writes to `invoice` / `contract` tables |

Two notes on the numbers. First, the README quotes rounder public figures (≥ 90%
found, ≥ 80% precision); the asserted CI thresholds above are the stricter ones
the harness actually enforces. Second, **money accuracy is not a percentage to
tune** — it is 100% or the build is broken.

## RAG metrics

**RAG** (retrieval-augmented generation) is the part that finds the right
paragraph of a long contract and puts it in front of the model. Retrieval is
scored separately from generation, because a model cannot answer well from the
wrong paragraph, and it is unfair to blame it for that.

| Metric | What it means |
|---|---|
| Retrieval precision | Of the clauses retrieved, how many were actually relevant |
| Retrieval recall | Of the clauses that should have been retrieved, how many were |
| Citation accuracy | Does the cited clause actually contain the fact claimed |
| Citation completeness | Are all the facts needed for the conclusion cited, not just some |

Retrieval uses hybrid search — semantic vector search combined with ordinary
full-text search, merged by reciprocal rank fusion — because legal phrases like
*"thirty (30) days' prior written notice"* are better matched lexically while
paraphrases are better matched semantically.

## Agent metrics

The investigation agent is scored on process, not just conclusions. A right
answer reached by an invalid route is not a right answer.

| Metric | Target shape | Why it matters |
|---|---|---|
| Tool-call accuracy | High | Each tool called with arguments that make sense for the question |
| Invalid tool-call rate | Near zero | Calls rejected by the schema, or not permitted by the read-only registry |
| Unsupported conclusion rate | Near zero | Conclusions not backed by a recorded tool result — the Verifier's core job |
| Investigation completion rate | High | Cases that reach a terminal state rather than exhausting budget |

Budget exhaustion is not a crash. It is a legitimate `terminal_reason` that
routes the case to `NEEDS_REVIEW`, and it is counted so that a budget that is too
tight is visible rather than silently degrading quality.

## Clause-extraction suite

This suite scores how well the system reads a real contract and pulls structured
facts out of lawyer prose. It is built on **~30 labelled clauses**, split into
**dev (10)** and **test (20)** and **frozen by hash** — the test split cannot be
adjusted once scored, or the score stops meaning anything.

Fields extracted include governing law, renewal term, notice period, auto-renew,
payment terms, price uplift cap, termination for convenience, exclusivity, most
favoured nation, minimum commitment, audit rights and cap on liability.

**Correctness rule.** For text-valued fields, an answer counts as correct if it is
a **normalised exact match** (case-folded, whitespace collapsed, punctuation
stripped) **or** reaches a **token-level F1 ≥ 0.9**. Numeric fields use numeric
equality after unit normalisation — *"thirty (30) days"* and *"Net 30"* both
become `30`.

**Grounding rule.** A correct value is not enough. The returned
`source_clause_id` must be present, and the extracted answer span must **overlap
the gold answer within ±200 characters**. This is what stops the model from
producing the right fact from the wrong place — which in a contract system means
it produced the right fact by luck, and will not reproduce.

**Abstention.** Roughly 20% of the 30 items are **negatives** — the clause is
absent from the contract. For those, abstaining is the **correct** answer and is
scored as correct. A model that always answers scores worse than one that knows
when to say nothing.

Reported per field: precision, recall, F1, exact-match accuracy, grounding rate,
and abstention correctness.

## Running the evaluation

```bash
make eval
```

This runs the suites and prints the scorecard:

| Suite | What it scores |
|---|---|
| `detection` | Precision, recall, F1 against `golden_label` |
| `exception_classification` | Legitimate exceptions correctly classified |
| `confidence_calibration` | Whether the `high` band deserves its name |
| `clause_extraction` | The ~30-item frozen clause suite |
| `qa_grounding` | Whether Q&A answers are grounded in the evidence pack |

Results are written to `eval_run` and `eval_result`, stamped with the `git_sha`
and `dataset_version`, so any historical score can be reproduced exactly. The
suites run offline (`LLM_MOCK=1`) and never touch the network.

## Optional: managed-RAG comparison baseline (TICKET-048)

Retrieval is hand-rolled on purpose — pgvector plus Postgres full-text search,
merged by reciprocal rank fusion — so the stack stays small and fully
reproducible. The trade-off is that we cannot claim our numbers are good in the
abstract; we can only claim they are good *relative to something*.

TICKET-048 adds an **optional, off-by-default** baseline: run the same retrieval
queries and the same clause-extraction suite through a managed retrieval service
and compare retrieval precision/recall, citation accuracy and grounding rate side
by side.

Constraints, because an optional benchmark must not become a hidden dependency:

- **Never a CI gate.** It does not run in `make eval` unless explicitly enabled,
  and a failure never fails the build.
- **Never a dependency of the product.** The local path is the only path that
  ships; nothing in the application imports the baseline.
- **Never a data egress.** It runs only against the synthetic corpus and the
  offline CUAD fixture — real contract text is never sent to a third party.
- **Never a replacement.** The purpose is to know whether the hand-rolled
  retriever is leaving accuracy on the table, and if so, by how much. A gap is a
  finding to report, not a reason to switch stacks mid-build.

If the comparison shows the local retriever is materially worse, that is a
result worth having — it is exactly the kind of thing that is much cheaper to
learn from a benchmark than from a customer.
