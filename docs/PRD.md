# Product Requirements Document — AI Revenue Leakage Investigator

## What this means

A software company sells subscriptions. The deal is written in a contract, but then
five different teams record it in five different systems — and over time those
records stop agreeing with each other. Nobody notices, because each team only looks
at their own system, and each system looks fine on its own.

The result is that the company is owed money it never invoices. This product finds
those gaps, works out what they are worth, proves it with evidence, and asks a
person in Finance to approve a fix. **It never fixes anything by itself.**

The genuinely hard part is not spotting that two numbers differ. It is telling the
difference between *"we are losing money"* and *"this customer has an approved
discount, which is fine"*. That distinction is the product.

---

## 1. The problem

### 1.1 Commercial truth fragments

A single customer's commercial reality is spread across five systems:

```
Contract  →  CRM  →  Implementation  →  Product Usage  →  Billing  →  Revenue
```

Each arrow is a place where information can be lost:

- A contract is signed, but the amendment that raised the seat count never reaches billing
- Sales records 100 seats in the CRM; implementation activates 100; billing is still set to 70
- A premium feature is switched on in the product but never added to the invoice
- A renewal increases the price, but the old price keeps being used
- A discount expires but is never removed
- A customer exists twice in the data, so half their subscription disappears

### 1.2 Nobody owns the gap

Revenue Operations owns CRM. Finance owns invoices. Sales Operations owns the
contract. Customer Success owns usage. **No single team owns the consistency
between them.** Reconciliation happens, if at all, during an annual audit — by
which time the loss has compounded for a year.

### 1.3 Why existing approaches fail

| Approach | Why it fails |
|---|---|
| Spreadsheet spot-checks | Samples a handful of accounts; the loss is in the long tail |
| Billing system reports | Billing is internally consistent. It cannot see that the contract disagrees with it |
| Generic BI dashboards | Show revenue going up or down, not *why it is lower than it should be* |
| Rules in the billing system | Only catch what someone thought to write a rule for |
| "Ask an AI chatbot" | Produces plausible narrative with no evidence and no verified numbers |

---

## 2. Users

| Role | What they need | Primary screen |
|---|---|---|
| **Finance analyst** | A queue of cases with enough evidence to decide quickly | Case queue, case detail |
| **Finance approver** | Confidence that the number is right before approving money | Case detail, decision panel |
| **Revenue operations** | Understand which system is the source of the error | Case detail, change timeline |
| **Sales operations** | Know when an amendment did not propagate | Case detail, evidence |
| **Billing operations** | Fix the underlying configuration error | Case detail, recommended action |
| **Customer success** | Warning before a renewal inherits the same bug | Customer risk view |

**Design consequence:** Finance is the primary user. Every screen must answer
*"can I trust this number, and what do I do about it?"* within a few seconds.

---

## 3. Product principles

1. **Code computes money. AI explains.** Never the reverse.
2. **No claim without evidence.** Every conclusion cites a specific record or clause.
3. **Propose, never execute.** Financial mutation always requires a human.
4. **Refusing is a valid answer.** "Cannot determine" is better than a confident guess.
5. **Distinguish anomaly from leakage.** The system's job is to reduce noise, not add to it.
6. **Everything is reconstructable.** Any decision can be replayed from the audit trail.

---

## 4. Scope

### 4.1 In scope (must have)

**Detection**
- Continuous reconciliation across Contract, CRM, Implementation, Usage, Billing
- Ten distinct leakage patterns (§5)
- Entity resolution so the same customer is comparable across systems
- Rule-based, trend, ratio and historical anomaly detection
- Idempotency: re-running never duplicates work

**Investigation**
- An agent that gathers structured records and contract clauses via read-only tools
- Deterministic financial impact calculation
- Evidence chain with citations and confidence
- Explicit handling of missing, conflicting and ambiguous evidence

**Human review**
- Case queue with filters
- Case detail with evidence, trace, timeline and recommended action
- Approve / reject / mark valid exception / request more investigation / assign / note
- Recovered-revenue ledger

**Assurance**
- Immutable audit trail
- Golden-dataset evaluation with published metrics
- Documented failure modes

### 4.2 Should have

- "What changed?" field-level diff timeline
- Customer Revenue Integrity Score (clearly labelled an internal operational metric)
- Time-to-detect simulator
- Constrained "ask the investigator" Q&A scoped to one case's evidence

### 4.3 Could have

- Cloudflare AI Search comparison baseline (purely a measurement exercise)
- Analytics views by product, root cause and source system

### 4.4 Explicitly out of scope

| Not doing | Why |
|---|---|
| Real Salesforce / Stripe / NetSuite integrations | Would require credentials and sandbox accounts; adapter interfaces are built instead |
| Issuing or correcting real invoices | The product proposes; a human acts in the billing system |
| Real authentication | Seeded roles only — enough to show permissions, not a security product |
| Multi-tenancy | Single-company internal tool |
| Machine-learning anomaly detection | At this data size, rules and statistics are more accurate *and* more explainable |
| Fine-tuning or training any model | We retrieve and read; we do not train |
| Usage-based pricing optimisation | Different product |

---

## 5. The ten leakage patterns

Each is generated deliberately so ground truth is known.

| # | Pattern | Plain description |
|---|---|---|
| 1 | `SEAT_UNDERBILLING` | Contracted 100 seats, billed 70 |
| 2 | `AMENDMENT_NOT_PROPAGATED` | Amendment raised 50 → 100 seats; billing still 50 |
| 3 | `PREMIUM_FEATURE_NOT_BILLED` | Premium feature active in product, absent from invoice |
| 4 | `RENEWAL_PRICE_NOT_APPLIED` | Renewal raised the price; invoice still uses the old one |
| 5 | `DISCOUNT_EXPIRED_STILL_APPLIED` | Discount expired but still being applied |
| 6 | `SERVICES_DELIVERED_NOT_INVOICED` | Paid implementation/professional services never invoiced |
| 7 | `BILLING_START_DATE_MISMATCH` | Contract start differs from billing start |
| 8 | `USAGE_EXCEEDS_ENTITLEMENT` | Usage consistently above contracted and billed entitlement |
| 9 | `SKU_RENAMED_NOT_REMAPPED` | Product SKU changed; billing still maps to the old one |
| 10 | `DUPLICATE_CUSTOMER_SPLIT` | Customer duplicated across systems; part of the subscription vanishes |

## 6. Legitimate exceptions

These look identical to leakage. Getting them right is the headline capability.

| Exception | Why it is not leakage |
|---|---|
| Approved discount | Contractually agreed lower price |
| Free pilot | Deliberate zero-charge trial period |
| Contractual grace period | Billing intentionally deferred by contract |
| Promotional period | Temporary agreed reduction |
| Usage-based pricing | Billed amount legitimately varies with consumption |
| Minimum commitment | Floor, not a per-seat charge |
| Delayed billing by contract | Start date intentionally later than signature |
| Credit memo | Deliberate reversal |
| Service included in subscription | Bundled, not separately chargeable |
| Temporary suspension | Agreed pause |
| Grandfathered expired discount | Discount expired but contractually allowed to continue |

Exceptions live in a **first-class registry** with scope and validity dates, so
"is this legitimate?" is a database lookup, not an AI opinion.

---

## 7. User journey — the hero case

1. Detection runs overnight. A mismatch is found for Acme Corporation.
2. A case is created: `RL-2026-00417`, type `AMENDMENT_NOT_PROPAGATED`.
3. Triage checks the exception registry. Nothing matches. Case goes to the agent.
4. The agent pulls the contract clause, the amendment, the CRM opportunity, the
   implementation record, the usage snapshot and the invoice line — each via a
   read-only tool, each recorded as evidence.
5. The verifier re-checks every number against the database. All pass.
6. Confidence is computed: **94%**. Recommendation drafted.
7. Finance opens the queue, sees one row with $18,000 at risk and 94% confidence.
8. Finance opens the case and reads: what changed, when, in which system, with
   the exact contract clause quoted.
9. Finance approves. The case moves to RESOLVED and $18,000 enters the recovered ledger.

Note what the system did **not** do: it did not touch the invoice.

---

## 8. Success criteria

| Measure | Target | Why it matters |
|---|---|---|
| Detection recall | ≥ 90% of injected cases found | Missing leakage defeats the purpose |
| Detection precision | ≥ 80% | False alarms destroy trust and the queue is ignored |
| Legitimate exceptions correctly classified | ≥ 8 of 10 | The headline capability |
| Money calculations | 100% correct | Finance cannot use approximate numbers |
| Citations point at real source text | ≥ 90% | Evidence that cannot be checked is not evidence |
| Cases >90% confidence confirmed by humans | ≥ 85% | Confidence must mean something |
| Zero duplicate cases on re-run | 100% | Otherwise the queue becomes noise |
| No code path can write to invoice/contract tables | Proven by test | The guardrail must be real |

---

## 9. Open questions and risks

| Risk | Mitigation |
|---|---|
| Synthetic data may not feel real | Real CUAD contract prose for the document layer |
| Contract-term extraction will need iteration | Dedicated labelled eval set from day one (TICKET-036) |
| Agent may be slow or expensive | Bounded tool/token budgets; job queue; mock provider for tests |
| Confidence scores may not calibrate | Dedicated calibration suite; gates can only lower scores |
| Public contracts are not SaaS contracts | Seat counts and prices are synthetic and layered on top |
| Scope may be too large for the time available | Tickets are dependency-ordered; phases 0–4 plus the hero scenario yield a demoable system |

---

## 10. Positioning

**Not** "an AI chatbot for finance."

**It is** *an AI-assisted revenue assurance system that reconciles commercial truth
across contracts, CRM, product usage, implementation and billing — with
deterministic money, verifiable evidence, and a human on every financial decision.*

The differentiating combination: cross-system reconciliation + contract-aware
reasoning + deterministic financial maths + entity resolution + evidence-backed
agent investigation + human-in-the-loop control + auditability.
