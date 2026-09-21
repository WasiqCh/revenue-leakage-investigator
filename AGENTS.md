# AGENTS.md — Rules for any coding agent working in this repository

These rules are **binding**, not suggestions. A change that violates any rule in
the "Hard rules" section will be rejected regardless of whether it works.

Read this file completely before writing any code.

---

## 0. Project orientation

We are building an **AI Revenue Leakage Investigator** for a B2B SaaS company.
It reconciles five systems (Contract, CRM, Implementation, Usage, Billing),
detects discrepancies, investigates them with an LLM agent, computes financial
impact with deterministic code, and proposes corrections for human approval.

Read in this order before starting:
1. `README.md` — what the product is, in plain English
2. `docs/PRD.md` — scope and requirements
3. `docs/TRD.md` — technical design
4. The ticket you are working on

---

## 1. Hard rules

### 1.1 The AI never computes money

- All financial arithmetic lives in `backend/app/money/` and `backend/app/billing/`.
- The LLM may **never** emit a currency amount, a seat count, a date, a quantity,
  or a percentage that ends up stored or displayed.
- The LLM may emit **text** and **one enum** (`contract_clarity`).
- If you find yourself parsing a number out of model output, stop — you are
  solving the wrong problem. Add a tool instead.

### 1.2 The AI cannot write to financial data

- The agent connects to Postgres using the `rl_readonly` role.
- Every agent tool must be declared read-only. Tools are defined in
  `backend/app/ai/tools.py` and each has `read_only=True` enforced by a test.
- No tool may create, update, or delete a `source_*` table row.
- The only writes the system performs are into `case`, `evidence`,
  `recommendation`, `investigation_report`, `agent_trace_step`, `audit_event`,
  `case_outcome` and `job` — and those go through the app role, not the agent.

### 1.3 Every number is verified

After the agent produces a report, `backend/app/ai/verifier.py` re-checks every
numeric claim against the database. Any claim not backed by a recorded tool
result is either dropped or downgrades the case to `NEEDS_REVIEW`.

### 1.4 Determinism

- Money uses `Decimal`, never `float`. Quantise to the currency's minor units
  with `ROUND_HALF_UP`.
- No `random` without an explicit seeded `Random(seed)`.
- No `datetime.now()` inside money or period logic. Functions take an
  `as_of_date` parameter.
- Running detection twice must produce identical results and create zero new
  cases.

### 1.5 Tests are not optional

- Every money function has unit tests and at least one Hypothesis property test.
- Every reconciliation rule has a passing case and a failing case.
- Every agent tool has a schema validation test.
- `make test` must be green before a ticket is marked complete.
- Tests never touch the network. Use `LLM_MOCK=1`.

---

## 2. Technical constraints

| Constraint | Rule |
|---|---|
| Language (backend) | Python 3.13, type hints everywhere, `mypy` clean |
| Language (frontend) | TypeScript, strict mode |
| Database | PostgreSQL 16 + pgvector. **Docker only.** No SQLite fallback. |
| ORM | SQLAlchemy 2.0 with `Mapped[]` annotations. Alembic for migrations. |
| Validation | Pydantic v2 models at every boundary |
| Agent | Hand-rolled loop in `backend/app/ai/agent_loop.py`. **Do not add** LangChain, LangGraph, PydanticAI, LlamaIndex, CrewAI or similar. |
| Orchestration | Postgres job table + worker. **Do not add** Celery, Redis, RabbitMQ, Kafka or n8n. |
| LLM access | Only through `backend/app/ai/provider.py`. Never call an SDK directly elsewhere. |
| HTTP | httpx, async where natural |
| Styling | Tailwind + shadcn/ui. No custom CSS framework. |

If a ticket seems to need a library not listed here, **stop and flag it** rather
than adding a dependency.

---

## 3. Working method

1. Work one ticket at a time, in numeric order.
2. Before writing code, re-read the ticket's acceptance criteria.
3. Create only the files the ticket names. Do not reorganise the repo.
4. When you finish, run `make test` and check every acceptance criterion.
5. Update the ticket file: mark criteria `[x]` and set `Status: DONE`.
6. Commit with a message referencing the ticket.

### Before you push

Run the evidence bundle and clear your own findings first:

```bash
make verify
```

It writes `artifacts/verify-report.md`. Nothing may be pushed while that report
contains a failure. Fix your own problems before someone else has to find them.

Two things this catches that self-review usually misses:

- **Tests that never ran.** Check the collected count in the report. A green run
  with zero tests collected is a failure, not a pass.
- **Pages that build but render empty.** `make routes` proves each page returns
  200 *and* contains the label that should be on it.

Full rules, severities and the gate schedule:
[`docs/verification-protocol.md`](docs/verification-protocol.md).

### Commit format

```
TICKET-014: implement billing period enumeration

Short body explaining what changed and why.

Refs: docs/tickets/TICKET-014-billing-period-enumeration.md

Co-authored-by: umer-ch817 <chumerha91@gmail.com>
```

The `Co-authored-by:` trailer is **required** on every commit.

---

## 4. What "done" means for a ticket

A ticket is complete only when **all** of these are true:

- [ ] Every file named in "Deliverables" exists
- [ ] Every acceptance criterion is met and checked off in the ticket file
- [ ] `make test` passes
- [ ] No hard rule in section 1 was violated
- [ ] No new dependency was added without being flagged
- [ ] Ticket file status updated to DONE

---

## 5. Common failure modes to avoid

- **Hallucinated numbers.** If the data is missing, set status to
  `NEEDS_REVIEW` and say so. Never guess.
- **Floating-point money.** `0.1 + 0.2 != 0.3`. Use `Decimal`.
- **Duplicate cases.** Always fingerprint before creating a case.
- **Dumping the whole contract into the prompt.** Retrieve specific clauses with
  citation metadata.
- **Confidence from the model.** Call `cases/confidence.compute_confidence()`.
- **Committing CUAD data.** The `.gitignore` blocks it. Do not override.
- **Writing to source tables.** Impossible via `rl_readonly`; if you find a way
  around it, that is a bug — report it, do not use it.

---

## 6. Uncertainty

If a ticket is ambiguous, or a requirement conflicts with a hard rule, **stop and
ask**. Do not guess, and do not silently pick one interpretation. It is far
cheaper to ask than to unpick a wrong assumption across 48 tickets.
