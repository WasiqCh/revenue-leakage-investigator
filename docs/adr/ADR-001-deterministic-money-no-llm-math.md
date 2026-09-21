# ADR-001: All money is computed in deterministic code, never by the language model

**Status:** Accepted — 2026-09-21

## What this means

Every dollar figure this product produces is calculated by ordinary Python code, not by the AI. The AI is a **large language model (LLM)** — a system that predicts plausible text. It is fluent, confident, and it does not reliably add up. It may read contracts and write explanations, and nothing else: it may not output a currency amount, seat count, date, quantity or percentage that we store or show. The one non-text thing it may output is a single labelled choice, `contract_clarity` — whether a contract's wording is Clear, Ambiguous or Missing. If an investigation needs a number, the AI must call a **tool**, a pre-written function that our code runs.

## Context

The product's whole value is that Finance can trust it, and one wrong figure destroys that. We are also asking a model to reason about lawyer prose, which is edge-of-competence work — exactly where fabricated numbers appear. Expected failures: shown `70 seats x $120` it reports `$8,300` because that looks plausible; it invents a proration it was never given; it rounds differently on two runs, so re-running detection changes a case. Both candidate designs let the model near the arithmetic.

## Decision

**All financial arithmetic is computed in Python using `Decimal`, and the LLM never emits a currency amount, seat count, date, quantity or percentage that is stored or displayed. It may emit free text and exactly one enum, `contract_clarity`.**

- Money and period maths live in `backend/app/money/` and `backend/app/billing/`, use `Decimal` (never `float`), and quantise to minor units with `ROUND_HALF_UP`.
- Tools return numbers from the database or from those modules; the model only chooses which tool to call and explains the result.
- `backend/app/ai/verifier.py` re-checks every numeric claim against recorded tool results. Unsupported numbers are dropped, or the case becomes `NEEDS_REVIEW`.
- A test asserts the model's output schema contains no numeric field other than the permitted enum.
- If you find yourself parsing a number out of model output, stop — you are solving the wrong problem. Add a tool instead.

## Alternatives considered

- **Let the model compute the money.** Rejected. Arithmetic is the one thing code guarantees and the one thing a language model does not, and a model's figure cannot be explained to an auditor.
- **Let the model compute, then verify with code.** Rejected. It produces both the right and the wrong answer and relies on the checker to pick, and it forces raw prices and seat counts into the prompt. Verification is not a substitute for one source of truth.
- **Let the model extract numbers and let code use them.** Rejected — the subtle version, and the one most teams ship. Extraction is still generation: `1,000` misread as `100` is a silent 10x error. We use retrieval and rule extractors with recorded provenance, and anything unsettled becomes an exception.
- **Ask the model to self-report a confidence percentage.** Rejected for the same reason. Confidence is computed by code from weighted factors; the model contributes one input.

## Consequences

**Easier.** Money is exact and reproducible. The Verifier has one clear rule to enforce. Correctness is provable with unit and property tests that never touch a model. Detection is idempotent, which is what lets us claim that re-running creates zero duplicate cases. An auditor can be shown the exact function behind any figure.

**Harder.** Materially more code: every quantity the report mentions needs a tool, so the tool surface is larger than if we simply asked the model. The model is also weaker at some tasks because it cannot sanity-check itself with a quick sum, so when tooling is incomplete it must report that it cannot proceed.

**Negative.** Tool design becomes a bottleneck. A missing tool stalls an investigation instead of letting it improvise. That friction is deliberate, but it is friction, and it will be felt during the first month of building.

## How to reverse it

We would have to accept approximate, non-reproducible financial figures, remove the Verifier's numeric checks, and drop the accuracy targets in `docs/evaluation.md` that assume exactness — rebuilding the credibility story, not just the code.
