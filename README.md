# AI Revenue Leakage Investigator

> **Status: design complete, code not yet written.**
> This repository currently contains the product and technical specification,
> the architecture, and 48 implementation tickets. The application code is built
> from those tickets. See [docs/tickets/README.md](docs/tickets/README.md).

---

## What this is (plain English)

A SaaS company sells 100 seats at $120 each. It is owed **$12,000 a month**.

But the deal is recorded in five different systems by five different teams:

| System | What it says |
|---|---|
| Contract | "100 seats at $120/seat/month" |
| CRM | "We sold 100 seats" |
| Implementation | "We activated 100 seats" |
| Product usage | "97 people logged in" |
| Billing | "Invoice for 70 seats" |

Every team looks at their own system and it looks fine. Nobody looks across all
five. So the invoice quietly says 70 seats — **$8,400**. The company loses
$3,600 every month and does not know.

This product is a **continuous auditor**. It reads all five systems, finds where
they disagree, works out what the disagreement is worth in money, proves it with
evidence, and hands a correction proposal to a human in Finance to approve.

**It never fixes anything by itself.** It only proposes.

---

## The three rules that make this credible

1. **Code does the money.** Never the AI. AI is bad at arithmetic. Every dollar
   figure is computed in Python using `Decimal`, and is unit-tested.
2. **AI reads and explains.** Contracts are written in lawyer prose. That is what
   AI is genuinely good at: extracting meaning and explaining it.
3. **Humans decide.** The system proposes. Finance approves, rejects, or marks
   the case a legitimate exception.

A useful way to hold it in your head: **AI is the investigator, code is the
accountant, the human is the judge.**

---

## What makes this more than "numbers don't match"

Most naive systems do this: *"the numbers differ, therefore we are losing money."*
That is wrong and it produces noise nobody trusts.

The hard part — and the headline capability here — is telling the difference between:

- **Real leakage** — we are owed money and not collecting it
- **Legitimate exception** — an approved discount, a free pilot, a grace period,
  a promotional price. Looks identical to leakage. Is not.
- **Ambiguous** — genuinely cannot be determined from the data. The correct answer
  is to say so and escalate to a human, not to guess.

---

## Quickstart

Requires **Docker** (there is no non-Docker path — see
[ADR-002](docs/adr/ADR-002-postgres-pgvector-docker-only.md)).

```bash
cp .env.example .env      # then fill in LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
make up                   # start database, API, worker, website
make seed                 # generate the synthetic company dataset
make reconcile            # run detection
make investigate          # run agent investigations
open http://localhost:3000
```

Everything at once, for a demo: `make demo`

Run the tests and the evaluation scorecard:

```bash
make test     # never touches the network
make eval     # precision / recall / citation accuracy / money accuracy
```

---

## Architecture in one picture

```
Contract repo ─┐
CRM ───────────┤
Implementation ├──► INGEST ──► CANONICAL MODEL ──► ENTITY RESOLUTION
Usage ─────────┤                                          │
Billing ───────┘                                          ▼
                                            RECONCILIATION + RULES + ANOMALY
                                                          │
                                                          ▼
                                                  CASE (deduped)
                                                          │
                                                          ▼
                                            INVESTIGATION AGENT (read-only tools)
                                                          │
                                                          ▼
                                                    VERIFIER  ◄── code re-checks
                                                          │       every number
                                                          ▼
                                        EVIDENCE + CONFIDENCE + RECOMMENDATION
                                                          │
                                                          ▼
                                              HUMAN REVIEW (approve / reject)
```

The **Verifier** is the part most people leave out. After the AI writes its
report, deterministic code re-checks every number in it against the database.
Any claim that is not backed by a real tool result is dropped, or the case is
downgraded to "needs review". This is what stops the AI from inventing figures.

Full detail: [docs/architecture.md](docs/architecture.md).

---

## Key decisions (already made — do not relitigate)

| Area | Decision | Why |
|---|---|---|
| Money | `Decimal`, never float. LLM never emits a number. | Money must be exact |
| AI scope | LLM reads contracts and writes explanations only | Right tool for the job |
| Guardrail | Agent connects to Postgres as a **read-only role** | "Never mutate an invoice" becomes a *permission*, not a promise |
| Confidence | Computed by code from 8 weighted factors; LLM contributes **one** input (`contract_clarity`) | A model self-reporting "94% confident" is meaningless |
| Database | PostgreSQL 16 + pgvector, **Docker only** | One datastore, real vector search |
| Orchestration | Hand-rolled Python loop. No LangChain, no n8n, no Celery/Redis | Testable, no framework churn, less infra |
| Dedup | A 5-month-old mismatch = **one** case, not five | Otherwise the queue is unusable |
| Ground truth | Synthetic data is generated *from* labelled scenarios | We know the right answer by construction, so evaluation is free |
| Real data | CUAD public contracts for text/testing **only** | Gives realistic prose + a free answer key |

Every decision has a full write-up in [docs/adr/](docs/adr/).

---

## Where the data comes from

**Synthetic (the bulk):** customers, contracts, amendments, CRM opportunities,
usage snapshots, invoices, implementation records. Generated from labelled
scenario templates so ground truth is known automatically. 50–100 customers,
12 months of history, 10 deliberate leakage patterns plus legitimate exceptions.

**Real (for testing only):** [CUAD](https://zenodo.org/records/4595826) — 510
real commercial contracts with ~13,000 lawyer-made clause labels, 105.9 MB.
Used to (a) give the search layer realistic legal prose and (b) provide a
ready-made answer key to score clause extraction.

> **We do not train any model.** We download text, split it into clauses, convert
> each clause into a vector using an existing embedding model, and search it later.
> That is retrieval, not training. See
> [docs/adr/ADR-007-cuad-real-data-non-redistribution.md](docs/adr/ADR-007-cuad-real-data-non-redistribution.md).
>
> CUAD contract text is **cached outside the repo and never committed**, because
> the dataset's licence is not clearly published. Synthetic customer names are
> used everywhere; real company names never reach the database or the UI.

---

## Repo layout

```
.
├─ README.md              ← you are here. Single source of truth.
├─ AGENTS.md              ← rules the coding agent must follow
├─ docker-compose.yml     database + API + worker + website
├─ Makefile               make up / seed / reconcile / test / eval / demo
├─ docs/
│  ├─ README.md           reading order for the docs
│  ├─ PRD.md              what we are building and why
│  ├─ TRD.md              how it is built
│  ├─ architecture.md     diagrams
│  ├─ data-model.md       every table, and what class of data it holds
│  ├─ billing-periods.md  the hardest part: dates and proration
│  ├─ confidence.md       how the confidence score is computed
│  ├─ case-lifecycle.md   the state machine
│  ├─ evaluation.md       how we prove it works
│  ├─ glossary.md         plain-English dictionary of every technical term
│  ├─ demo-script.md      click-by-click script for the demo video
│  ├─ adr/                one file per significant decision
│  └─ tickets/            one file per unit of work (48 total)
├─ backend/               FastAPI application (to be built)
├─ frontend/              Next.js application (to be built)
├─ scripts/fetch_cuad.py  downloads the real dataset
└─ fixtures/golden/       the labelled test set
```

---

## How work gets done

1. Read [docs/PRD.md](docs/PRD.md) then [docs/TRD.md](docs/TRD.md).
2. Work through [docs/tickets/](docs/tickets/) in numeric order. Each ticket is
   small enough to finish and verify on its own.
3. Follow [AGENTS.md](AGENTS.md). It is not advisory — it contains hard rules
   (no LLM for money, no writes from the agent, tests required).
4. A ticket is done only when its acceptance criteria pass and `make test` is green.

---

## What "done" looks like

| Measure | Target |
|---|---|
| Finds real leakage | ≥ 90% of injected cases |
| Avoids false alarms | ≥ 80% precision |
| Correctly identifies legitimate exceptions | ≥ 8 of 10 |
| Money calculations | 100% correct, no rounding drift |
| Citations point at real text | ≥ 90% |
| Cases scored >90% confidence confirmed by humans | ≥ 85% |
| Running detection twice | creates zero duplicate cases |
| Can any code path write to invoice/contract tables? | No — proven by test |

---

## People

- **Wasiq** (`wasiqch`) — product scope, specification, review, testing.
- **Umer** (`umer-ch817`) — implementation. Listed as co-author on every commit.

## Licence

MIT — see [LICENSE](LICENSE). Note that the CUAD dataset is third-party and is
never redistributed here; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
