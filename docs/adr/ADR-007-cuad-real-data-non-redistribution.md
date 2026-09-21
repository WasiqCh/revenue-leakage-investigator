# ADR-007: CUAD real contracts for retrieval and evaluation, never redistributed

**Status:** Accepted — 2026-09-21

## What this means

We need contracts written like real contracts, because text we invent reads nothing like lawyer prose and would not prove that the extraction or retrieval parts of this system work. We therefore use a public research dataset called **CUAD** — the Contract Understanding Atticus Dataset — which holds 510 real commercial contracts with roughly 13,000 clauses already labelled by type. It is a single 105.9 MB archive, `CUAD_v1.zip`, from Zenodo record 4595826. We use it for two things: realistic legal text for the search layer to retrieve, and a ready-made answer key so we can score whether clause extraction found the right clauses. **We do not train any model on it.** We download the text, split it into clauses, convert each clause into a vector using an existing embedding model, and search those vectors later. That is retrieval, not training. Three conditions apply. The licence is not clearly published on either the Zenodo record or the GitHub repository, so `scripts/fetch_cuad.py` must read it from inside the archive and **fail loudly** if it cannot determine one. Contract text is cached outside the repository and blocked by `.gitignore`, and is never committed. And the contracts name real companies from public SEC filings (EDGAR), whose names never reach our `customer` table or the UI — synthetic names only.

## Context

Two needs pull in opposite directions. The demo needs legal text that behaves like the real thing, because clause extraction from invented prose is a much easier problem and we would be marking our own homework. But this is a small team publishing open source, and the honest position on a dataset with no clear licence is that we may use it locally and must not pass it on. CUAD fits the first need well: it is the standard benchmark for contract clause extraction, so the answer key is lawyer-made rather than ours, which makes our numbers comparable to published ones. The handling concerns are equally clear. The archive is large, so committing it would bloat the repository permanently. The licence is genuinely unclear, so redistributing it could be a real legal problem. And the contracts contain identifiable third-party company names and commercial terms we have no reason to expose. There is one limitation we state rather than let a reader discover: CUAD's contracts are generic commercial agreements — distribution, franchise, licensing, services — not SaaS subscription agreements. They discuss territories and royalties, not seat counts and per-seat prices.

## Decision

**Use CUAD (Zenodo record 4595826, `CUAD_v1.zip`, 105.9 MB, md5 `c38f490a984420b8a62600db401fafd5`) for realistic contract prose and as a labelled answer key for clause-extraction evaluation. Never redistribute it. Never train on it.**

- `scripts/fetch_cuad.py` downloads the archive, verifies the md5, reads the licence from inside it, and exits non-zero with a clear message if the licence cannot be determined. It does not guess.
- Extracted text caches outside the repository, defaulting to `~/.cache/revenue-leakage-investigator/cuad/`; `.gitignore` also blocks `cuad/`, `*.zip` and `CUAD_v1*` inside the repo as a second line of defence.
- No CUAD text is committed. `THIRD_PARTY_NOTICES.md` records the source, version, checksum and licence position.
- Real party names are stripped at ingest. `customer` rows come from synthetic name lists, the real-to-synthetic mapping never leaves the pipeline, and no UI surface renders a real EDGAR party name.
- Seat counts and prices are synthetic, layered on top of CUAD prose, because CUAD contracts do not contain them.
- Embeddings come from a third-party embedding model at ingest time. No model weights are fine-tuned, trained or updated from this data.

## Alternatives considered

- **Generate synthetic contracts with a language model.** Rejected. Cheaper and licence-free, but generated prose is uniformly well-structured and well-behaved, so extraction accuracy on it is close to meaningless and it hides exactly the failures retrieval must survive.
- **Hand-write a small set of realistic contracts.** Rejected. Slow and expensive, and still authored by the same people who wrote the extractor, so it is not an independent answer key.
- **Use CUAD and commit the text to the repository.** Rejected. An unclear licence plus a 105.9 MB binary is both a legal and a practical problem.
- **Use CUAD and ignore the licence question.** Rejected. This is the tempting shortcut, and precisely the kind of decision that becomes a liability. A script that fails loudly is cheap; a takedown request is not.
- **A different dataset with clear licensing (LEDGAR, MAUD, ContractNLI).** Considered, not chosen now. LEDGAR is a genuine fallback if CUAD must be removed; MAUD is narrower; ContractNLI targets entailment rather than extraction. CUAD remains the best-known extraction benchmark, which is what makes the comparison worth more.
- **Keep the real party names and simply not show them.** Rejected. "Stored but hidden" is one refactor away from "stored and displayed", and no product requirement needs the real name.

## Consequences

**Easier.** Retrieval is exercised against genuinely hard text. Clause extraction has an independent, lawyer-made answer key, so precision and recall figures mean something and can be compared to published results. The evaluation suite gets a real corpus without us writing one, and nothing shipped depends on a network fetch at runtime.

**Harder.** Onboarding requires a 105.9 MB download and an embedding pass before the retrieval tests are meaningful, so the first run is slow. The pipeline must carry a name-stripping step a synthetic-only approach would not need, and every contributor must understand that the dataset is present locally and absent from the repository — an easy thing to get wrong.

**Negative.** The licence position is unresolved, so we cannot bundle CUAD, cannot ship a container that includes it, and cannot promise a demo environment has it; the demo therefore depends on a fetch step. And the dataset does not match the domain: CUAD's clauses are adjacent to, not the same as, SaaS subscription clauses, so seat counts and prices are synthetic. Our clause-extraction numbers are real, but the money-extraction story is layered on top and evaluation readers must know which half is measured and which half is constructed.

## How to reverse it

Removing CUAD means swapping the corpus provider in the ingest layer, regenerating embeddings, and re-baselining extraction evaluation — a contained change, since no product logic depends on CUAD specifically. Adding a redistributable dataset later is the same swap plus a notices update.
