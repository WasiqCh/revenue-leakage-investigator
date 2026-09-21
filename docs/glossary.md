# Glossary

Plain-English definitions of every technical term used in this project.

If you are not an engineer, read this file first. Everywhere else in the
documentation assumes you know these words. Each entry gives the term, a
definition a smart non-engineer can follow, and — where it helps — one line on
why it matters *here*.

Grouped into six sections:

1. Money and numbers
2. Data and databases
3. Search and AI
4. The agent
5. Process and workflow
6. Testing and measurement

---

## 1. Money and numbers

**ACT/ACT**
Actual over actual. A way of splitting a month's charge fairly across part of a
month by counting the real number of days involved, rather than assuming every
month has 30 days.
*Why it matters here:* it is how we work out what a customer should be charged
when their plan starts or ends mid-month.

**Anchor date**
The day of the month a billing cycle is pinned to. If the anchor date is the
15th, every billing period runs from the 15th to the 14th of the next month.
*Why it matters here:* two customers on the same price can be owed different
amounts in the same calendar month, purely because their anchor dates differ.

**ARR**
Annual Recurring Revenue. The value of a subscription expressed as a yearly
figure. A $1,000-per-month subscription is $12,000 ARR.
*Why it matters here:* leakage figures are easier to compare when annualised, so
the case queue can rank a small problem on a big contract above a big problem on
a tiny one.

**Billing period**
The block of time one invoice is supposed to cover — usually one month, but it
can be a quarter or a year.
*Why it matters here:* almost every question in this product is really "what
should this customer have been charged *for this window of time*".

**Canonical data model** (see also section 2)
The one agreed shape we translate all five source systems into before comparing
them.

**Credit memo**
A document that reduces what a customer owes — effectively a negative invoice.
*Why it matters here:* a credit memo is often the *correct* explanation for a
billing figure that looks too low, so mistaking one for leakage produces a false
alarm.

**Decimal vs float**
Two ways a computer stores numbers. `float` is approximate — it cannot represent
0.1 exactly, so `0.1 + 0.2` does not equal `0.3`. `Decimal` is exact.
*Why it matters here:* money is stored and computed with `Decimal` only. Floating
point errors would eventually show up as a one-cent discrepancy in a report to
Finance, and that destroys trust in the whole system.

**Deterministic**
The same inputs always produce exactly the same output, every time, on every
machine.
*Why it matters here:* running detection twice must produce identical numbers and
create zero duplicate cases. Anything non-deterministic is a bug.

**Entitlement**
What a customer is contractually allowed to use — for example, 100 seats or
unlimited API calls.
*Why it matters here:* a customer using more than their entitlement may be
under-billed, and a customer using less may indicate seats were never activated.

**FX rate**
Foreign exchange rate — the conversion factor between two currencies on a given
day.
*Why it matters here:* customers pay in different currencies, so everything is
converted to one reporting currency before totals are added up.

**Half-open interval**
A date range that includes its start date but excludes its end date. Written
`[1 April, 1 May)`, meaning 1 April up to but not including 1 May.
*Why it matters here:* it is the only way to make monthly periods line up exactly
with no gaps and no double-counting of a single day.

**Idempotent**
Doing something twice has the same effect as doing it once.
*Why it matters here:* re-running reconciliation must never duplicate a case.
Every write in the pipeline is built to be safely repeatable.

**Minor units**
The smallest unit of a currency — cents for dollars, pence for pounds.
*Why it matters here:* all money is stored as a whole number of minor units, so
there is never a fraction of a cent to argue about.

**Proration**
Charging only the fair share of a period. If a plan starts on the 15th of a
30-day month, the customer owes roughly half that month.
*Why it matters here:* getting proration wrong invents money that was never owed,
or hides money that was.

**Reporting currency**
The single currency all figures are converted into for reporting and comparison.
*Why it matters here:* totals across customers are meaningless unless they are in
one currency.

**Revenue assurance**
The business discipline of checking that you actually bill and collect everything
you are entitled to.
*Why it matters here:* this product is a revenue assurance tool — an automated,
continuous version of a job normally done by spreadsheet.

**Revenue leakage**
Money a company is contractually owed but never bills or never collects. It is
silent: each individual team's system looks correct on its own.
*Why it matters here:* it is the entire subject of the product. The README's
example — 100 seats sold, 70 billed, $3,600 lost every month — is revenue leakage.

**Reconciliation**
Comparing two sets of records to find where they disagree.
*Why it matters here:* it is the core operation. Contract is compared against CRM,
against implementation, against usage, against billing.

**ROUND_HALF_UP**
A rounding rule: exactly half rounds up. 2.5 becomes 3, and −2.5 becomes −3.
*Why it matters here:* it is the fixed, documented rounding rule everywhere in the
money code, so two runs can never disagree by a cent.

**SCD-2 / slowly changing dimension**
A standard data-warehouse technique for keeping history. Instead of overwriting a
record when it changes, you close the old version with an end date and open a new
version with a start date.
*Why it matters here:* we must be able to answer "what did the contract say *in
April*", not just "what does it say now".

**Seat**
One named user licence. 100 seats means 100 people may use the product.
*Why it matters here:* seats are the unit in the headline example. Billing 70
seats when 100 were contracted is the classic leak.

**SKU**
Stock Keeping Unit — a unique code identifying a specific product or plan.
*Why it matters here:* if a SKU is renamed in one system but not another, the
systems stop matching and a subscription can appear to vanish.

**Upsert**
A combined "update or insert": if the record exists, update it; if it does not,
create it.
*Why it matters here:* cases are upserted by fingerprint, which is what makes
repeated runs safe.

---

## 2. Data and databases

**Alias**
An alternative name for the same thing. "Acme Corp" and "ACME Corporation Ltd"
are aliases of one customer.
*Why it matters here:* aliases are the reason naive name matching fails, and the
reason we need entity resolution.

**Alembic**
The standard tool for managing database structure changes in Python projects.
*Why it matters here:* every change to the database schema is delivered as an
Alembic migration, so any machine can be brought to the same shape.

**Canonical data model**
One agreed set of tables and field names that all five source systems are
translated into before anything is compared.
*Why it matters here:* without it, every comparison would need custom code for
every pair of systems.

**Chunk** / **Chunking**
Splitting a long document into smaller pieces so it can be stored and searched.
*Why it matters here:* contracts are split into clauses rather than whole
documents, because retrieving one relevant clause is far more useful than
retrieving a 60-page PDF.

**Dedup** / **Deduplication**
Removing duplicates.
*Why it matters here:* the same mismatch repeating for five months is one case,
not five.

**Docker**
A tool that packages an application and everything it needs into a container, so
it runs identically on any machine.
*Why it matters here:* there is no non-Docker setup. `make up` starts everything.

**Docker Compose**
The file that describes the four containers this project runs: database, API,
worker, website.

**Entity resolution**
Working out that two records in two different systems refer to the same real
thing, even when the names differ.
*Why it matters here:* "Acme Corp" in the CRM and "ACME Corporation Ltd" in
billing are one customer. Until that is established, every comparison is
meaningless.

**Fingerprint**
A short code computed from a record's identifying fields, used to recognise the
same record again later.
*Why it matters here:* a case fingerprint deliberately ignores the billing period,
so the same ongoing mismatch is recognised as one case.

**Migration**
A versioned, repeatable change to the database structure — adding a table,
adding a column, and so on.

**ORM**
Object-Relational Mapper. A library that lets code talk to database tables as if
they were ordinary objects.
*Why it matters here:* we use SQLAlchemy 2.0, and the same model definitions are
the source of truth for the schema.

**pgvector**
An add-on for PostgreSQL that lets the database store and search vectors
(see section 3).
*Why it matters here:* it gives us real semantic search without running a
separate search service.

**Postgres / PostgreSQL**
The relational database this project uses. Version 16.
*Why it matters here:* it is the single datastore — records, cases, jobs, vectors
and audit trail all live in it.

**Seed data**
The starting dataset loaded into an empty database so the app has something to
work with.
*Why it matters here:* `make seed` generates the whole synthetic company.

**Synthetic data**
Fake data generated to look realistic, used instead of real customer data.
*Why it matters here:* it is generated from labelled recipes, so we know the
correct answer for every customer by construction — which makes evaluation free.

**Vector**
A list of numbers that represents the meaning of a piece of text, produced by an
embedding model. Similar meanings produce similar vectors.

---

## 3. Search and AI

**Citation**
A reference from a claim back to the exact source it came from — here, a
specific evidence row and the text excerpt inside it.
*Why it matters here:* every claim in an investigation report must carry one. A
claim without a citation is not allowed to survive the verifier.

**Clause**
A single numbered or headed section of a contract — for example "3.2 Fees" or
"7.1 Renewal Term".
*Why it matters here:* clauses are the unit of retrieval and citation. We retrieve
clauses, not whole contracts.

**Context window**
The maximum amount of text a language model can consider at once.
*Why it matters here:* contracts are far too long to fit, which is exactly why we
retrieve only the relevant clauses instead of pasting the whole document in.

**Embedding**
The process (and the result) of turning text into a vector so that similar
meanings end up close together in number-space.
*Why it matters here:* it lets us search contracts by meaning, so "we can raise
the price each year" finds a clause headed "Escalation".

**Grounding**
Keeping an AI's output tied to real, retrieved source material rather than to the
model's memory.
*Why it matters here:* grounded output can be checked; ungrounded output cannot.
The verifier exists to enforce grounding on every number.

**Hallucination**
When an AI states something confidently that is not true and is not supported by
any source.
*Why it matters here:* it is the single biggest risk in this product. A made-up
dollar figure in a Finance report would be catastrophic, which is why the AI never
emits numbers and every claim is re-checked.

**Hybrid search**
Running two different kinds of search at once and combining the results.
*Why it matters here:* meaning-based search misses exact terms; keyword search
misses paraphrases. Combining them finds more.

**Keyword search**
Finding documents that contain the exact words you typed. Also called lexical or
full-text search.
*Why it matters here:* a clause mentioning a specific defined term ("Minimum
Commitment") is best found this way.

**LLM**
Large Language Model. The AI model that reads text and writes text.
*Why it matters here:* it is used for exactly two jobs: reading contract prose,
and writing explanations in plain English. Never arithmetic.

**Prompt**
The instruction and context given to a language model for one call.
*Why it matters here:* prompts live in version-controlled files under
`backend/app/ai/prompts/` so changes to them are reviewable.

**RAG**
Retrieval-Augmented Generation. Look up the relevant real text first, then give
that text to the AI and ask it to answer using only what it was given.
*Why it matters here:* it is how the AI reads contracts without inventing terms.

**Reciprocal rank fusion (RRF)**
A simple, robust formula for merging two ranked result lists into one. Each
result scores `1 / (constant + its rank)` in each list, and the scores are added.
*Why it matters here:* it merges the keyword and semantic result lists without
needing to calibrate their scores against each other.

**Reranking**
Taking a shortlist of search results and reordering it with a more careful (and
more expensive) method.
*Why it matters here:* it improves which clause ends up at the top, which matters
because only a few clauses fit in the model's context window.

**Semantic search**
Searching by meaning rather than by exact words.
*Why it matters here:* a question about "early termination penalties" should find
a clause headed "Termination for Convenience" that never uses the word "penalty".

**Structured output**
Asking a model to reply in a strict, machine-readable shape — specific fields,
specific allowed values — instead of free prose.
*Why it matters here:* it is how the AI is forced to reply with text and one
label, and is structurally prevented from emitting a number.

**Token**
The unit language models read and bill in. Roughly three-quarters of a word.
*Why it matters here:* investigations have a token budget, and exceeding it stops
the investigation rather than running up an unbounded bill.

---

## 4. The agent

**Agent**
An AI that is given a goal and a set of permitted actions, and works in steps
towards that goal rather than answering in one shot.
*Why it matters here:* the agent investigates a discrepancy: it decides what to
look up, looks it up, and reasons towards an explanation.

**Agent loop**
The repeating cycle the agent follows: plan, gather evidence, form a hypothesis,
test it, conclude.
*Why it matters here:* it is hand-written code with hard limits, not a framework.
It always terminates, and every step is recorded.

**Audit trail**
A permanent, append-only record of who did what and when.
*Why it matters here:* every case state change writes exactly one audit event, so
the history of a case can always be reconstructed.

**Confidence gate**
A hard rule that *caps* a confidence score regardless of how good everything else
looks. For example, if the verifier found a problem, the score cannot exceed 60.
*Why it matters here:* gates can only ever lower a score, never raise it. That
makes them a safety mechanism rather than a scoring trick.

**Confidence score**
A number from 0 to 100 saying how much the system trusts its own conclusion.
*Why it matters here:* it is computed by deterministic code from eight weighted
factors. The AI contributes exactly one of those factors — how clearly the
contract is worded — and nothing else. A model reporting its own confidence would
be meaningless.

**Evidence chain**
The ordered set of facts that supports a conclusion, each one traceable to a
source record.
*Why it matters here:* it is what a Finance reviewer actually reads before
approving a correction.

**Hypothesis**
A proposed explanation for a discrepancy, which the agent then tries to confirm
or rule out.
*Why it matters here:* "billing configuration not updated after amendment AM-1042"
is a hypothesis; the agent must find evidence before it can be stated as the root
cause.

**Read-only role**
A database user account that is permitted to read data but forbidden by the
database itself from changing anything.
*Why it matters here:* it turns "the AI will never modify an invoice" from a
promise into a permission the database enforces.

**Tool calling**
The mechanism by which an AI asks the surrounding program to run a specific
function and give it the result.
*Why it matters here:* the agent can only ask questions through registered tools.
It has no other channel.

**Tool registry**
The fixed, named list of tools the agent is allowed to call, each with a strict
input shape and a declared read-only flag.
*Why it matters here:* it is the agent's entire vocabulary. It cannot ask anything
that is not on the list, and every tool is proven read-only by a test.

**Verifier**
The component that re-checks every numeric claim in the AI's report against the
database, after the AI has finished.
*Why it matters here:* it is the most important safety part of the system. A claim
not backed by a recorded tool result is dropped, and the case is downgraded to
needs review.

---

## 5. Process and workflow

**Anomaly detection**
Flagging something that looks unusual compared with normal patterns, without
knowing in advance what the problem is.
*Why it matters here:* rules catch the patterns we already know about; anomaly
detection is the safety net for the ones we do not.

**Approval**
The human act of accepting a proposed correction so it can be applied outside the
system.
*Why it matters here:* approval can only ever be performed by a human actor. The
state machine refuses any other actor type.

**Backoff**
Waiting longer between each retry after a failure, instead of hammering a service.
*Why it matters here:* a failing LLM call is retried with increasing delays, then
given up on.

**Billing configuration not updated**
A common real-world root cause: a signed amendment changed the deal, but the
billing system was never updated to match. Nothing is "broken" — a human simply
did not do a step.
*Why it matters here:* it is the root cause of the headline demo case.

**Case**
One ongoing problem with one customer, tracked from detection through to a human
decision.
*Why it matters here:* it is the unit of work in the queue. One case covers the
whole affected period, not one month.

**Dead-letter**
A holding area for jobs that failed repeatedly and will not be retried
automatically.
*Why it matters here:* a permanently broken job is parked for a human instead of
blocking the queue forever.

**False positive**
A warning that turns out to be wrong — the system cried wolf.
*Why it matters here:* too many false positives and Finance stops reading the
queue. Suppressing them is a headline feature, not a nice-to-have.

**Human-in-the-loop**
A design where a person must review and decide before anything actually changes.
*Why it matters here:* the system only ever proposes. A human approves, rejects,
or marks the case a legitimate exception.

**Job queue**
A list of background tasks waiting to be picked up and run by a worker.
*Why it matters here:* it lives in a Postgres table. No Redis, no Celery.

**Legitimate exception**
A difference that looks exactly like leakage but is intentional and approved — a
discount, a free pilot, a grace period, a grandfathered price.
*Why it matters here:* telling these apart from real leakage is the hardest part
of the product and the main thing the demo proves.

**LLM provider**
The company or service that actually runs the language model.
*Why it matters here:* all model access goes through one adapter module, so the
provider can be swapped without touching any other code.

**State machine**
A formal map of which states a thing may be in and which moves between them are
legal.
*Why it matters here:* a case can only move along allowed edges. Illegal moves are
rejected outright, and every legal move writes an audit event.

**Worker**
A long-running background process that takes jobs off the queue and runs them.
*Why it matters here:* investigations are slow, so they run in a worker and the
website stays responsive.

---

## 6. Testing and measurement

**CI**
Continuous Integration. An automated service that runs linting and tests every
time code is pushed.
*Why it matters here:* CI runs with no network access, so a test that silently
depends on the internet fails immediately rather than mysteriously.

**CUAD**
Contract Understanding Atticus Dataset. 510 real commercial contracts annotated
by lawyers with about 13,000 clause labels, published on Zenodo.
*Why it matters here:* it gives the search layer realistic legal prose to work
with, and a ready-made answer key for scoring clause extraction. It is third-party
data with an unclear licence and is never redistributed — see
[../THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

**End-to-end test**
A test that drives the whole system from start to finish, as a user would.
*Why it matters here:* one test goes from an empty database all the way to an
approved case, proving the pieces fit together.

**F1**
A single score combining precision and recall into one number. Useful when you
care about both kinds of mistake.
*Why it matters here:* clause extraction is graded on exact match or token-F1
above 0.9.

**Golden dataset**
A fixed, hand-checked set of inputs with known correct answers, used as the
reference for grading.
*Why it matters here:* because our synthetic data is generated from labelled
recipes, the golden dataset is correct by construction.

**Ground truth**
The known, correct answer for a given input.
*Why it matters here:* every injected leak has a recorded ground truth, so we can
measure whether the system found it.

**Hypothesis** (the library)
A Python library that generates many random-but-valid inputs to test a rule, and
shrinks any failing case to the smallest example that still fails.
*Why it matters here:* it is how we prove date and money logic is correct for all
anchor days, all month lengths, and all boundary values — not just the few
examples a human thought to write down.

**Integration test**
A test that checks several components working together, often with a real
database.
*Why it matters here:* it is how we prove reconciliation is idempotent and that
the verifier catches a fabricated number.

**Precision**
Of the things the system flagged, the fraction that were genuinely problems.
High precision means few false alarms.
*Why it matters here:* the target is at least 0.80 in production terms and 0.90 on
the seeded golden set.

**Property-based test**
A test that states a rule which must always hold, then checks it against hundreds
of randomly generated inputs.
*Why it matters here:* "confirmed leakage never exceeds historical leakage" is a
property. It is checked across many generated cases rather than one example.

**Recall**
Of the real problems that exist, the fraction the system actually found. High
recall means few misses.
*Why it matters here:* the target is at least 0.90 of injected cases found, and
0.95 on the seeded golden set.

**Scenario template**
A reusable recipe describing one kind of problem: which systems disagree, by how
much, and what the correct answer is.
*Why it matters here:* the synthetic dataset is generated from these, which is why
ground truth is known automatically.

**Seed** (random)
The number that makes a random generator reproducible. The same seed always
produces the same sequence.
*Why it matters here:* every random operation takes an explicit seed. Running the
generator twice with the same seed produces byte-identical output.

**Unit test**
A test of one small function in isolation.
*Why it matters here:* every money function has unit tests plus at least one
property test.

---

## Where to go next

- What the product is, in plain English: [../README.md](../README.md)
- How it is built: [architecture.md](architecture.md)
- Why each big decision was made: [adr/](adr/)
- How to run it: [runbook.md](runbook.md)
- How to demo it: [demo-script.md](demo-script.md)
