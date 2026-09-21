# ADR-008: Synthetic data is generated from labelled scenario templates

**Status:** Accepted — 2026-09-21

## What this means

Almost all the data this system runs on is invented by us, in a specific way: we start from **scenario templates**, which are recipes describing a situation and the correct answer for it. One template says "the contract sells 100 seats, CRM records 100, implementation activated 100, usage shows 97, billing invoiced 70 — this is real leakage of 30 seats". Another says "the contract has an approved promotional discount documented in an amendment, so the low invoice is a legitimate exception, not leakage". There are ten leakage scenarios plus a set of exception-only scenarios. A generator reads each template and produces the matching rows across all five systems — contract, CRM, implementation, usage and billing — with consistent customers, dates and amounts. The benefit is **ground truth by construction**: ground truth means the known correct answer, and because we know the recipe we know the answer for every generated case without anyone labelling data by hand, which is how evaluation datasets are normally built and is slow, expensive and error-prone. The golden evaluation set is therefore a free byproduct of seeding the database. The limitation is equally clear: this data can only show that we find the leak types we thought to encode, and it cannot discover leakage patterns nobody has imagined.

## Context

To claim the system works we must measure it: what fraction of real leakage it found, how often it cried wolf, whether it recognised legitimate exceptions. Each measure needs a labelled answer key, and for real customer data that key does not exist — that is the entire reason the product is needed. Hand-labelling a few hundred cases is work nobody on this project will do well or enjoy. There is a sharper problem too. The hardest capability here is separating real leakage from a legitimate exception: a discount, a free pilot and a grace period all look exactly like under-billing. If we generate data by randomly perturbing numbers, that distinction does not exist in the data at all, so we would be measuring nothing. It has to be *built into* the generation, which means generating from templates that encode the reason, not just the numbers. The cost is a real and specific blind spot: our evaluation measures our own imagination. We are choosing to pay that cost knowingly.

## Decision

**All synthetic data is generated from labelled scenario templates, and the golden evaluation dataset is derived from those templates rather than labelled separately.**

- Templates live in `fixtures/` and declare, per scenario, the leak or exception type, the systems involved, the intended correct verdict, the expected money impact, and the evidence that should make the verdict discoverable.
- The generator takes an explicit seed and `as_of_date`; no unseeded `random`, no wall-clock calls. The same seed produces byte-identical data.
- Ten leakage patterns are covered, plus exception-only scenarios for approved discounts, free pilots, grace periods and promotional pricing.
- The golden set is written to `fixtures/golden/` with the expected verdict and money impact attached, so scoring is a join rather than a judgement.
- Some customers are generated with no defect at all, so precision is measured against a realistic noise floor rather than a dataset that is entirely faults.
- A template with no corresponding evaluation case fails the build, so the two cannot silently drift apart.

## Alternatives considered

- **Hand-label real or semi-real data.** Rejected. The most credible option and not affordable here — and it cannot produce the exception cases, because the reason an invoice is low is usually absent from the data, which is the problem the product solves.
- **Random perturbation of a clean dataset.** Rejected. It produces numbers that differ without producing reasons, so it cannot exercise the real-leakage versus legitimate-exception distinction, and it generates physically impossible combinations that the reconciliation layer rejects before the interesting code runs.
- **Generate everything with a language model.** Rejected. Non-deterministic, so the evaluation is not reproducible, and the model's idea of a plausible discrepancy is not a controlled set of leak types.
- **CUAD contracts plus synthetic numbers, with no scenario layer.** Rejected as insufficient on its own. CUAD gives realistic clause text, which is what ADR-007 is for, but it carries no billing history and no known verdict, so it cannot serve as ground truth for leakage detection.
- **Real anonymised customer data.** Rejected. We do not have any, and acquiring it would require a customer, a data processing agreement and a conversation this project is not positioned to have.

## Consequences

**Easier.** The evaluation suite exists from day one and costs nothing to extend: adding a leak type means adding a template, and the golden case appears with it. Ground truth is exact rather than approximate. Runs are reproducible from a seed, so a score change is attributable to a code change rather than to data drift. Exception scenarios can be constructed deliberately, which is the only way to test the hardest capability. The dataset holds no personal or third-party data, so it can be committed and shared freely.

**Harder.** Every new leak type is a template someone must design, so evaluation quality is bounded by template quality. The generator is itself code that needs tests, because a bug in the generator silently corrupts ground truth and would make the product look better or worse than it is. Keeping templates and golden cases in step requires the coverage check described above.

**Negative.** The blind spot is structural. A high score on this dataset means the system finds the leakage patterns we encoded; it says nothing about a pattern we did not imagine. Every evaluation number must be reported with that caveat, and it is the honest answer to "how do you know it works on real data": we know it works on the ten failures we can construct, and we designed the system so that anything it cannot determine becomes a human review rather than a guess. There is also a risk of overfitting to the templates without realising, since the extractors and the generator are written by the same people.

## How to reverse it

Replacing synthetic data with real data means providing a labelled corpus, moving the answer key out of the generator and into an annotation pipeline, and accepting that the exception scenarios may no longer be distinguishable — at which point the precision targets in `docs/evaluation.md` must be re-derived rather than carried over.
