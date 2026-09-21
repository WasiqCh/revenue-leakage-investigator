# Verification protocol

How each ticket gets checked before the project moves on.

---

## What this means

Nobody should be guessing whether a ticket actually works. This document says
exactly what gets checked, when, by whom, and what happens when something fails.

The key idea: **most checking is done by running a command, not by a person
reading code.** Umer does not need to open a browser or interpret output. His
agent runs `make verify`, and the result is a file.

---

## 1. Who does what

| Layer | Who | Needs Docker | What it covers |
|---|---|---|---|
| **Self-check** | Umer's agent, before pushing | yes | `make verify` must pass clean |
| **Tier 1** | Verification agent, after pulling | **no** | Static rules: deliverables, guardrails, forbidden patterns |
| **Tier 2** | Umer's agent, at gates | yes | Tests, migrations, build, route smoke, evaluation |

Tier 1 is deliberately runnable on a machine with no Docker, so verification does
not depend on any one person's setup.

---

## 2. Gate schedule

Default: a gate every five tickets.

| Gate | After ticket | Must be true to continue |
|---|---|---|
| G1 | 005 | Stack boots; migrations apply; source schema present |
| G2 | 010 | Dataset generates deterministically with golden labels |
| G3 | 015 | Expected revenue computes without reading invoices |
| G4 | 020 | Detection finds the injected discrepancies |
| G5 | 025 | Cases dedupe; exceptions route correctly |
| G6 | 030 | Agent investigates; verifier rejects invented numbers |
| G7 | 035 | Contract clauses are retrieved and cited |
| G8 | 040 | API works; permissions enforced; Q&A refuses properly |
| G9 | 045 | Interface usable; evaluation harness reports metrics |
| G10 | 050 | Everything green end to end |
| G11 | 052 | Final: all four new tickets complete |

### Verified individually, not batched

These are checked the moment they are finished, because everything downstream
depends on them or because they are guardrails:

**007** read-only role · **008** money primitives · **015** expected revenue ·
**022** case dedup · **026** confidence · **030** verifier

A batch gate never replaces an individual check on these six.

---

## 3. The evidence bundle

One command, run by Umer's agent:

```bash
make verify
```

It writes **`artifacts/verify-report.md`** and `artifacts/verify-report.json`.
The agent pastes or commits the Markdown file. What it contains:

- `docker compose ps` — every service healthy
- `alembic upgrade head` then `downgrade base` then `upgrade head` — migrations round-trip
- `pytest -q` — **including the number of tests collected**
- `next build`, `tsc --noEmit`, `eslint` — frontend compiles and typechecks
- route smoke test — every page returns 200 and renders its expected label
- git commit range covered

**The collected-test count is mandatory.** The single most common failure mode in
AI-generated code is a green suite in which zero tests actually ran. A summary
without that number is rejected.

---

## 4. Verifying the frontend without a browser

Frontend work is where a human is normally needed. Encoded instead:

| Check | Catches |
|---|---|
| `next build` | Broken imports, invalid routes, render-time crashes |
| `tsc --noEmit` | `any` leaks, wrong prop types |
| `eslint` | React mistakes, hooks misuse |
| `scripts/smoke_routes.sh` | Pages that build but render empty |

The smoke test curls each route, asserts HTTP 200, and asserts that an expected
label appears in the HTML — for example "Potential leakage" on the overview and
"Awaiting Finance review" on a case. That proves a screen actually rendered its
content, without anyone opening a browser.

Only **visual** review needs a person, and that is one screenshot at G9.

---

## 5. Severity

| Severity | Definition | Action |
|---|---|---|
| **SEV1** | Guardrail broken, money wrong, tests do not run, build fails, agent can write to source tables | **Stop immediately and ask.** Nothing proceeds until decided |
| **SEV2** | Acceptance criterion unmet, missing deliverable, dedupe or state-machine bug | Must be fixed before the next gate |
| **SEV3** | Style, naming, missing docstring, minor duplication | Warn and continue |
| **SEV4** | Observation or suggestion | Log only |

**Escalation rule:** any SEV1 halts the gate and asks whether to fix it first.
Three or more SEV2s also triggers a recommendation to stop. Severity is about
danger, not tidiness — correctness and guardrails are non-negotiable, style is
never a blocker.

---

## 6. What gets checked (Tier 1, no Docker)

`scripts/verify_ticket.py` automates all of this and prints `file:line` for
every finding.

**Deliverables** — every file the ticket names exists.

**Guardrails (SEV1)**
- `float` arithmetic in money or billing modules
- `Decimal(0.1)` constructed from a float instead of a string
- any write to a `source_*` table, or `UPDATE`/`DELETE` on invoice or contract
- banned dependency in `pyproject.toml`: LangChain, LangGraph, PydanticAI,
  LlamaIndex, CrewAI, Celery, Redis, n8n
- read-only role missing or unused

**Correctness traps (SEV1 / SEV2)**
- `datetime.now()` or `utcnow()` inside money, period or case logic
- unseeded `random`
- `os.environ` read outside `config.py`
- network calls in tests without a mock
- `except Exception: pass` hiding a failure
- hardcoded threshold or weight that should come from config
- half-open interval handled inclusively (off-by-one at a period boundary)

**Tests that prove nothing (SEV1)**
- tests that assert the implementation rather than the requirement
- tests so heavily mocked they pass when the feature is broken
- **tests that never run** — wrong filename, async without a plugin, `testpaths`
  mismatch. Detected via the collected count

**Process**
- commit subject references the ticket
- `Co-authored-by: umer-ch817 <chumerha91@gmail.com>` present
- ticket file criteria ticked and status updated

---

## 7. Verdicts

| Verdict | Meaning |
|---|---|
| **PASS** | Tier 1 clean and Tier 2 evidence attached |
| **FAIL** | A SEV1 or SEV2 found — returned with file and line |
| **BLOCKED** | Cannot be confirmed without a Docker run; awaiting evidence |
| **NEEDS EVIDENCE** | Code looks right but nothing proves it behaves correctly |

A ticket that cannot be fully checked locally is **BLOCKED, never PASS**. That
distinction is the whole point of the protocol — guessing is worse than waiting.

**No ticket is marked DONE until both tiers pass.**

---

## 8. Records

- **`docs/verification-log.md`** — chronological. Every entry: date, gate, commit
  range, what was checked, each finding with severity, verdict.
- **`docs/tickets/VERIFICATION.md`** — the scoreboard. One row per gate and per
  critical ticket.

The log is the evidence. The scoreboard is the status.

---

## 9. Self-check before pushing

Umer's agent must run `make verify` and clear its own SEV1s **before** pushing a
ticket. Independent verification then catches what self-review missed, instead of
doing first-line cleanup. This rule is in `AGENTS.md` and is binding.
