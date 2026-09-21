"""Regenerates docs/tickets/TICKET-*.md from the definitions in this file.

Maintenance utility — the ticket Markdown files are the source of truth, not this
script. Use it only when you need to rebuild every ticket consistently, for
example after changing the ticket template or renumbering.

    python scripts/generate_tickets.py

The `T` list below holds every ticket: number, title, phase, effort, dependencies,
goal, plain-English summary, technical context, deliverables and acceptance
criteria. Editing an entry here and re-running rewrites all 52 files, so keep the
definitions authoritative — do not hand-edit the generated Markdown and then
re-run, or your edits will be lost.

To add a ticket: append a `t(...)` call, then re-run.
"""
import os
from pathlib import Path

# Repo root, derived from this file's location: <root>/scripts/generate_tickets.py
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "docs" / "tickets"

T = []


def t(num, title, phase, effort, deps, goal, plain, context, deliverables, criteria, notes=None):
    T.append(dict(num=num, title=title, phase=phase, effort=effort, deps=deps,
                  goal=goal, plain=plain, context=context,
                  deliverables=deliverables, criteria=criteria, notes=notes or []))


# ---------------------------------------------------------------- Phase 0
t(1, "Repo scaffold, tooling and CI skeleton", "0 - Foundation", "0.5 day", [],
  "Establish the monorepo layout, linting, formatting, type checking and test configuration.",
  "Set up the workshop before building anything: folder layout, code style rules, and an "
  "automated check that runs on every change so bad code is caught immediately.",
  "ruff + mypy (strict on app/) for Python, eslint + prettier for TypeScript, pytest for "
  "tests. CI runs lint and unit tests without needing network access or any service "
  "beyond Postgres.",
  ["backend/pyproject.toml", "frontend/package.json", ".github/workflows/ci.yml",
   ".gitignore", "Makefile", "backend/tests/", "frontend/"],
  ["`make lint` exits 0 on a clean checkout",
   "`make test` exits 0 on an empty test suite",
   "ruff reports zero errors",
   "mypy reports zero errors on `app/`",
   "eslint reports zero errors"])

t(2, "Docker Compose stack", "0 - Foundation", "0.5 day", ["TICKET-001"],
  "Bring up Postgres 16 + pgvector, backend, worker and frontend with healthchecks.",
  "One command starts the whole app. Docker is the only supported way to run this "
  "project - there is deliberately no lightweight fallback, so every developer runs "
  "the same environment.",
  "Four services: db (pgvector/pgvector:pg16), backend, worker, frontend. Named volumes "
  "persist data. Healthchecks gate startup order. `scripts/init_db.sql` enables the "
  "vector, pg_trgm and pgcrypto extensions.",
  ["docker-compose.yml", "backend/Dockerfile", "frontend/Dockerfile", "scripts/init_db.sql"],
  ["`docker compose up -d` reaches all-healthy",
   "`psql -c \"select extname from pg_extension\"` includes `vector`",
   "backend `/healthz` returns 200",
   "frontend serves on port 3000"])

t(3, "Settings and environment contract", "0 - Foundation", "0.5 day", ["TICKET-001"],
  "Typed settings object covering every configurable value in the system.",
  "All the knobs in one place, with clear names. If something important is missing, "
  "the app refuses to start rather than silently guessing.",
  "Pydantic v2 `Settings`. Covers database URL, LLM base URL / key / model, reporting "
  "currency, money tolerances, confidence weights, agent budgets, and the CUAD "
  "source / cache / offline flags.",
  ["backend/app/config.py", ".env.example", "backend/tests/unit/test_config.py"],
  ["missing DATABASE_URL raises a validation error naming the field",
   "every setting is documented in .env.example",
   "a test asserts defaults for tolerances and confidence weights match the documented constants",
   "no code reads os.environ directly outside config.py"])

t(4, "Database engine, session and model conventions", "0 - Foundation", "1.0 day",
  ["TICKET-002", "TICKET-003"],
  "SQLAlchemy 2.0 engine, session factory, declarative base, custom column types and "
  "Alembic wired to the model metadata.",
  "The plumbing that lets the app talk to the database, plus special column types so "
  "money and date ranges are stored safely rather than as loose numbers.",
  "Custom types: MoneyType (Decimal), CurrencyCode, HalfOpenDateInterval helpers. "
  "Async engine. Alembic autogenerate configured against the shared metadata object.",
  ["backend/app/db/engine.py", "backend/app/db/session.py", "backend/app/db/base.py",
   "backend/app/db/types.py", "backend/app/db/enums.py", "alembic.ini", "alembic/env.py"],
  ["`alembic upgrade head` succeeds on an empty database",
   "a test round-trips a Decimal money column with 4 decimal places with no float drift",
   "`alembic check` reports no pending model diffs"])

# ---------------------------------------------------------------- Phase 1
t(5, "Source-domain schema and migration", "1 - Schema", "1.5 day", ["TICKET-004"],
  "All source and normalized tables with indexes and natural-key uniqueness.",
  "Create the tables that hold the raw business records: customers, contracts, "
  "products, invoices, usage and so on - exactly as the outside systems report them.",
  "Tables: customer, customer_alias, product, product_alias, pricing_rule, fx_rate, "
  "contract, contract_clause, contract_term, amendment, amendment_term, subscription, "
  "subscription_line, implementation, usage_snapshot, invoice, invoice_line, "
  "credit_memo, crm_opportunity.",
  ["backend/app/models/source/", "one Alembic revision",
   "backend/tests/integration/test_schema_source.py"],
  ["migration up / down / up succeeds",
   "a duplicate (source_system, source_id) raises IntegrityError in a test",
   "every table has id, created_at, updated_at",
   "a metadata test enumerates the expected table set exactly"])

t(6, "Derived, case and ops schema and migration", "1 - Schema", "1.5 day", ["TICKET-005"],
  "All remaining tables, plus the pgvector index and full-text index.",
  "Create the tables the system itself produces: billing periods, reconciliation "
  "results, investigation cases, evidence, audit events and job bookkeeping.",
  "Tables: billing_period, reconciliation_run, reconciliation_result, case, case_period, "
  "evidence, investigation_run, investigation_report, recommendation, agent_trace_step, "
  "audit_event, case_outcome, approved_exception, change_event, entity_resolution_match, "
  "golden_label, job, llm_call, eval_run, eval_result, qa_message. pgvector index on "
  "contract_clause.embedding, GIN index on tsv.",
  ["backend/app/models/derived/", "backend/app/models/case/", "backend/app/models/ops/",
   "one Alembic revision", "backend/tests/integration/test_schema_derived.py"],
  ["migration up / down / up succeeds",
   "case.case_key is unique",
   "reconciliation_result is unique on (run_id, customer, line, period, check_code)",
   "EXPLAIN on a vector similarity query uses the vector index"])

t(7, "Read-only role and immutability guards", "1 - Schema", "0.5 day", ["TICKET-006"],
  "Provision a SELECT-only database role and add triggers that block edits to audit data.",
  "This is the safety gate. The AI connects to the database with an account that is "
  "physically unable to change an invoice or a contract - so 'the AI never changes "
  "financial data' is a fact enforced by the database, not a promise in a comment.",
  "Role `rl_readonly` gets SELECT only on source tables. BEFORE UPDATE OR DELETE "
  "triggers block writes to audit_event and agent_trace_step, making evidence "
  "effectively append-only.",
  ["scripts/init_db.sql (role section)", "backend/app/db/guards.py",
   "backend/tests/integration/test_immutability.py"],
  ["a test connecting as rl_readonly gets 'permission denied' on UPDATE invoice",
   "UPDATE audit_event raises",
   "the application role can still insert normally",
   "no code path grants write access to the agent role"])

t(8, "Money and interval primitives", "1 - Schema", "1.0 day", ["TICKET-004"],
  "Currency-aware Decimal money type, FX helpers, and half-open date interval algebra.",
  "The maths building blocks. Money is stored as exact decimals (never floating point, "
  "because 0.1 + 0.2 is not 0.3 in floats and that error compounds in financial "
  "reports). Date ranges are treated as start-inclusive, end-exclusive so periods "
  "never overlap or leave gaps.",
  "DecimalMoney with add / multiply / quantize using ROUND_HALF_UP and per-currency "
  "minor units. Interval operations: intersect, subtract, length, merge.",
  ["backend/app/money/decimal_money.py", "backend/app/money/interval.py",
   "backend/app/money/fx.py", "backend/tests/unit/test_money.py",
   "backend/tests/property/test_interval.py"],
  ["Hypothesis proves interval length is additive under partitioning",
   "Hypothesis proves subtract never yields a negative length",
   "a test asserts Decimal never degrades to float",
   "FX walk-back returns the nearest prior business day and raises when none exists"])

# ---------------------------------------------------------------- Phase 2
t(9, "Scenario template registry", "2 - Data generation", "1.0 day", ["TICKET-005"],
  "Typed definitions for each leakage pattern and each legitimate-exception pattern.",
  "Write down, in code, every kind of problem we want the system to find - and every "
  "kind of 'this looks wrong but is actually fine' case. This list is the recipe book "
  "the fake data is generated from.",
  "Ten leak types plus at least four exception-only scenarios (approved discount, free "
  "pilot, grace period, grandfathered expired discount). Each declares which systems "
  "drift, which evidence should exist, and the expected root cause.",
  ["backend/app/generate/scenarios.py", "backend/tests/unit/test_scenarios.py"],
  ["all 10 leak types are present",
   "at least 4 exception types are present",
   "each spec validates against Pydantic and names its expected evidence set",
   "a test asserts the set of leak_type values matches the LeakType enum exactly"])

t(10, "Customer, contract and subscription generator", "2 - Data generation", "1.5 day",
  ["TICKET-009"],
  "Seeded generator producing customers, contracts, subscriptions and subscription lines.",
  "Generate a realistic fake company from a scenario recipe. Because we generate the "
  "data from a known recipe, we automatically know the right answer - which is what "
  "makes the testing later possible.",
  "Same seed always produces identical output. Subscription lines use slowly-changing-"
  "dimension versioning so history is preserved. Names are synthetic.",
  ["backend/app/generate/core.py", "backend/tests/property/test_generator_invariants.py"],
  ["same seed produces an identical output hash",
   "line effective ranges never overlap within a subscription",
   "subscription dates always fall inside contract dates",
   "a test asserts generated names match the synthetic pattern (no real companies)"])

t(11, "Usage, invoice and billing generators with injected drift", "2 - Data generation",
  "1.5 day", ["TICKET-010"],
  "Generate operational records, then inject the specific drift the scenario calls for.",
  "Create the invoices and usage logs, then deliberately break them in the exact way "
  "the recipe says - so billing says 70 seats while everything else says 100.",
  "Produces usage snapshots, invoices, invoice lines, credit memos, implementation "
  "records, CRM opportunities and pricing rules, then applies the drift.",
  ["backend/app/generate/drift.py", "backend/tests/integration/test_generated_data.py"],
  ["for each leak type the generated database state reproduces the intended discrepancy exactly",
   "a test recomputes the expected difference from raw rows and matches the manifest",
   "exception scenarios produce an approved_exception row and no discrepancy"])

t(12, "Ground-truth manifests, golden labels and seed command", "2 - Data generation",
  "1.0 day", ["TICKET-011"],
  "Emit per-customer answer keys, load them as golden labels, expose the seed CLI.",
  "Alongside the fake data, write down the answer sheet: which customers have real "
  "leakage, how much, and which ones are fine. Later we grade the system against it.",
  "Manifests are emitted per customer and loaded into golden_label. `make seed` and "
  "`python -m app.cli seed --seed N --customers M` are the entry points.",
  ["backend/app/generate/manifest.py", "backend/app/cli.py (seed command)",
   "fixtures/golden/", "backend/tests/integration/test_seed_determinism.py"],
  ["running seed twice with the same seed leaves row counts unchanged and manifest bytes identical",
   "golden_label row count equals the number of expected findings",
   "`make seed` is idempotent"])

# ---------------------------------------------------------------- Phase 3
t(13, "Billing period engine", "3 - Deterministic core", "1.5 day", ["TICKET-008"],
  "Enumerate billing periods with anchor modes, clamping and billable-start resolution.",
  "Work out exactly which time window each invoice should cover. This sounds trivial "
  "and is not: a deal signed 15 March with 'billing starts the first full period' "
  "means March is partly unbilled on purpose - and getting that wrong invents or hides "
  "real money.",
  "Implements anchors (calendar month, anniversary, contract effective day), backward "
  "clamping for anchor days 29-31, frequency stepping, stable period_index, and the "
  "three commencement overrides (immediate, first full period, next period start). "
  "See docs/billing-periods.md.",
  ["backend/app/billing/periods.py", "backend/tests/unit/test_periods.py",
   "backend/tests/property/test_period_clamping.py"],
  ["Hypothesis over anchor days 1-31 across months proves periods are contiguous, "
   "non-overlapping and cover the horizon",
   "anchor day 31 clamps in February and the next period resumes on the 31st",
   "FIRST_FULL_PERIOD produces zero March stub billing in the documented worked example"])

t(14, "Proration engine", "3 - Deterministic core", "1.0 day", ["TICKET-013"],
  "Compute partial-period amounts using ACT/ACT day counts and mid-period splitting.",
  "If a customer is billed for half a month, charge exactly half. Uses real calendar "
  "days, and splits a period into pieces when the quantity changes partway through.",
  "factor = billed_days / period_days, quantised to 2 decimal places with ROUND_HALF_UP. "
  "Mid-period quantity changes split at each change date; each piece is prorated and summed.",
  ["backend/app/billing/proration.py", "backend/tests/unit/test_proration.py",
   "backend/tests/property/test_proration.py"],
  ["the worked example yields $6,000 expected for 15 of 30 days",
   "splitting a period at a change date and summing equals prorating the whole period "
   "when quantity is constant",
   "no float appears anywhere in the module"])

t(15, "Expected revenue engine", "3 - Deterministic core", "1.5 day", ["TICKET-014"],
  "Compute what the customer should have been charged for a given line and period.",
  "This is the number everything is measured against: given the contract, its "
  "amendments, the price rules and the proration, what should the invoice have said?",
  "Composes contract terms, amendments, pricing rules, entitlement quantity and "
  "proration. Price lookup precedence is by priority then specificity. Critically, this "
  "function must never read invoice tables - otherwise it would 'agree' with the very "
  "error it is meant to catch.",
  ["backend/app/billing/expected_revenue.py",
   "backend/tests/unit/test_expected_revenue.py"],
  ["for every generated leak type the engine's expected value matches the manifest",
   "a test proves the function never reads invoice or invoice_line (query-log assertion)",
   "price precedence is deterministic across shuffled rule insertion order"])

t(16, "Detector framework and idempotent persistence", "3 - Deterministic core", "1.0 day",
  ["TICKET-015", "TICKET-006"],
  "A registry of checks that write reconciliation results without ever duplicating them.",
  "The reusable machinery every comparison plugs into. Running it twice must never "
  "create duplicate findings - otherwise the case queue fills with repeats and nobody "
  "trusts it.",
  "Registry maps check_code to a callable. Results are keyed for idempotency. Tolerances "
  "come from config, and each run is stamped with a config hash so a changed "
  "configuration is traceable.",
  ["backend/app/detect/framework.py", "backend/app/detect/checks/registry.py",
   "backend/tests/integration/test_reconciliation_idempotency.py"],
  ["running reconciliation twice on the same data creates zero duplicate rows",
   "tolerance boundary behaves as specified (exactly at tolerance passes, just over fails)",
   "an unknown check_code raises"])

t(18, "Detectors batch 1", "3 - Deterministic core", "2.0 days", ["TICKET-016"],
  "Implement seat underbilling, renewal price not applied, amendment not propagated, "
  "and premium feature not billed.",
  "The four most common ways companies lose money: fewer seats billed than sold, an "
  "old price still in use after a renewal, a signed amendment never reaching billing, "
  "and a paid feature switched on but never charged for.",
  "Each detector is a pure function over the canonical model that emits a "
  "reconciliation_result when its condition holds.",
  ["backend/app/detect/checks/seat_underbilling.py",
   "backend/app/detect/checks/renewal_price.py",
   "backend/app/detect/checks/amendment_propagation.py",
   "backend/app/detect/checks/premium_feature.py",
   "backend/tests/integration/test_checks_batch1.py"],
  ["each detector fires exactly on its generated scenario",
   "each produces zero false positives across 100 clean generated customers",
   "each has a Hypothesis test for boundary quantities and prices"])

t(19, "Detectors batch 2", "3 - Deterministic core", "2.5 days", ["TICKET-016", "TICKET-017"],
  "Implement expired discount, services not invoiced, start-date mismatch, usage "
  "over-entitlement, SKU rename and duplicate-customer split.",
  "Six more patterns, including the ones that catch honest mistakes (a discount that "
  "expired but is still being applied) and data chaos (one customer split across two "
  "records, so part of their subscription vanishes).",
  "Same shape as batch 1. The expired-discount detector must consult the exception "
  "registry so a grandfathered discount is not reported as leakage.",
  ["backend/app/detect/checks/discount_expiry.py",
   "backend/app/detect/checks/services.py",
   "backend/app/detect/checks/start_date.py",
   "backend/app/detect/checks/usage_entitlement.py",
   "backend/app/detect/checks/sku_rename.py",
   "backend/app/detect/checks/duplicate_split.py",
   "backend/tests/integration/test_checks_batch2.py"],
  ["each detector fires exactly on its generated scenario and no others",
   "DISCOUNT_EXPIRED_STILL_APPLIED does NOT fire when an approved_exception "
   "grandfathers the discount (asserted explicitly)",
   "zero false positives across 100 clean generated customers"])

t(20, "Period-boundary to dollar conversion and double-billing", "3 - Deterministic core",
  "1.0 day", ["TICKET-014", "TICKET-016"],
  "Turn date mismatches into money, and detect the same period being billed twice.",
  "A one-month gap between contract start and billing start is not a vague problem - "
  "it is a specific number of days times a daily rate. Also catches the opposite "
  "error: over-billing, which must be reported separately and never quietly netted off.",
  "Uses interval algebra and daily_rate = period_amount / period_days. Over-billing "
  "yields a negative delta surfaced as its own finding.",
  ["backend/app/detect/checks/period_boundary.py",
   "backend/tests/unit/test_period_boundary.py"],
  ["the documented worked example returns $6,000",
   "a leading-gap case returns the correct positive amount",
   "a billed-early case returns a negative (over-billing) delta",
   "a synthetic duplicate-coverage case is detected with the correct summed amount"])

t(17, "Entity resolution", "3 - Deterministic core", "1.0 day", ["TICKET-005"],
  "Match the same customer or product across systems that name it differently.",
  "'Acme Corp' in the CRM, 'ACME Corporation Ltd' in billing and 'Acme Corporation' on "
  "the contract are one customer. Until we prove that, every comparison is meaningless.",
  "Exact id, exact name, domain and fuzzy name matching. Writes entity_resolution_match "
  "with a confidence; auto-accepts above the high threshold, flags needs_review in the "
  "middle band so a human can confirm.",
  ["backend/app/detect/entity_resolution.py",
   "backend/tests/unit/test_entity_resolution.py"],
  ["exact ids always auto-accept",
   "a DUPLICATE_CUSTOMER_SPLIT scenario yields one needs_review match",
   "false-match rate on generated clean pairs is zero"])

t(21, "Change event generation (what changed)", "3 - Deterministic core", "1.0 day",
  ["TICKET-005"],
  "Record field-level diffs across versions of lines, terms and amendments.",
  "Not just 'billing says 70' but 'billing was changed to 70 on 3 May by the billing "
  "system, while the contract had already been amended to 100 on 1 April'. That "
  "sequence is what lets Finance act.",
  "Diffs slowly-changing-dimension versions of subscription lines, contract terms and "
  "amendments, writing change_event rows with changed_by and change_source.",
  ["backend/app/changefeed/diff.py",
   "backend/tests/integration/test_change_events.py"],
  ["changing a subscription line quantity produces exactly one change_event with correct old and new values",
   "re-running produces no duplicate events",
   "events are ordered by changed_at"])

# ---------------------------------------------------------------- Phase 4
t(22, "Case fingerprinting and idempotent upsert", "4 - Cases and money", "1.0 day",
  ["TICKET-016"],
  "Collapse a repeating mismatch into one case with an affected-period range.",
  "If the same 30-seat gap persists for five months, that is one ongoing problem, not "
  "five separate tickets. Without this the review queue becomes unusable and Finance "
  "stops reading it.",
  "case_key is a deterministic hash over (customer, subscription_line, leak_type, "
  "product) that intentionally ignores the period. Upsert extends the affected range "
  "and appends case_period rows.",
  ["backend/app/cases/fingerprint.py", "backend/tests/integration/test_case_dedup.py"],
  ["a mismatch persisting 5 periods yields exactly one case with affected_period_count == 5",
   "re-running detection leaves the case count unchanged",
   "two different leak types on the same line yield two cases"])

t(23, "Case lifecycle state machine", "4 - Cases and money", "1.0 day", ["TICKET-022"],
  "Implement the allowed transitions between case states with actor validation.",
  "A strict map of how a case may move - detected, investigated, awaiting review, "
  "approved, rejected. Illegal moves are rejected, and every move is recorded.",
  "Single transition() function with an allowed-edge table, actor type checks and "
  "audit emission. See docs/case-lifecycle.md.",
  ["backend/app/cases/state.py", "backend/tests/unit/test_state_machine.py",
   "backend/tests/property/test_state_machine.py"],
  ["Hypothesis proves no reachable illegal state",
   "every legal edge is exercisable in tests",
   "every transition writes exactly one audit_event",
   "APPROVED can only be entered when actor_type is 'human'"])

t(24, "Leakage maths and FX normalisation", "4 - Cases and money", "1.5 day",
  ["TICKET-023", "TICKET-008"],
  "Compute expected, actual, potential, historical, confirmed and annualised leakage.",
  "The money layer. Crucially it separates 'might be lost' from 'we are confident' "
  "from 'we actually got it back' - three different numbers that must never be "
  "conflated in a report to Finance.",
  "Recurring cases annualise as latest_delta x 12 / frequency_months; one-off cases "
  "annualise to themselves. FX uses the rate as of the relevant date, walking back to "
  "the nearest prior business day. See docs/evaluation.md.",
  ["backend/app/cases/leakage.py", "backend/app/money/fx.py",
   "backend/tests/unit/test_leakage.py",
   "backend/tests/property/test_money_conservation.py"],
  ["confirmed never exceeds historical (property test)",
   "a 5-period recurring case annualises to latest_delta x 12",
   "a one-off case annualises to itself",
   "a period with no usable FX rate is flagged insufficient_data and excluded from totals"])

t(25, "Exception registry and triage lookup", "4 - Cases and money", "1.0 day", ["TICKET-006"],
  "Store approved exceptions with scope and validity dates, and look them up during triage.",
  "A first-class list of 'this customer is allowed to be different' - an approved "
  "discount, a free pilot, a grace period. When a mismatch matches one of these, the "
  "system closes it as a valid exception without wasting an AI investigation.",
  "Scope matching across customer / subscription / subscription_line / product / global, "
  "combined with period overlap. Expired exceptions do not match.",
  ["backend/app/cases/exceptions.py", "backend/tests/unit/test_exception_lookup.py"],
  ["an exception covering the period routes the case to VALID_EXCEPTION with zero LLM calls",
   "an expired exception (effective_to before period_start) does not match",
   "a global-scope exception matches all customers"])

t(26, "Confidence engine", "4 - Cases and money", "1.5 day", ["TICKET-024", "TICKET-006"],
  "Compute the confidence score from weighted factors plus hard gates.",
  "Trust must be earned and measured, not asserted. The AI is allowed to contribute "
  "exactly one thing - how clearly the contract is worded. Everything else is measured "
  "from data, and hard rules can only ever lower the score.",
  "Eight weighted factors plus five gates. See docs/confidence.md for the exact "
  "weights and the gate behaviour.",
  ["backend/app/cases/confidence.py", "backend/tests/unit/test_confidence.py",
   "backend/tests/property/test_confidence_determinism.py"],
  ["identical inputs produce an identical score",
   "a verifier failure caps the score at 60",
   "a missing required evidence type caps it at 74",
   "a clean deterministic case floors at 85",
   "band boundaries at 75 and 90 behave exactly as specified"])

# ---------------------------------------------------------------- Phase 5
t(27, "LLM provider adapter, mock provider and call ledger", "5 - AI layer", "1.5 day",
  ["TICKET-003", "TICKET-006"],
  "A single OpenAI-compatible client with retries, structured output and a mock for tests.",
  "One front door for all AI calls, configured by environment variables so any "
  "compatible provider can be swapped in. Every call is logged with its token cost, "
  "and tests use a stand-in that never touches the network.",
  "Timeouts, bounded retries, JSON-mode structured output, token accounting into "
  "llm_call, and an in-process MockProvider.",
  ["backend/app/ai/provider.py", "backend/app/ai/prompts/",
   "backend/tests/unit/test_provider.py"],
  ["all tests run with MockProvider and zero network calls",
   "a forced server error triggers exactly the configured number of retries",
   "every call writes one llm_call row with token counts",
   "malformed JSON output raises a typed error"])

t(28, "Read-only tool registry", "5 - AI layer", "1.5 day", ["TICKET-007", "TICKET-027"],
  "Define the investigation tools the agent may call, all read-only and evidence-producing.",
  "Give the AI a fixed set of questions it is allowed to ask (fetch this contract clause, "
  "fetch these invoice lines). It cannot ask anything else, cannot write anything, and "
  "each answer is recorded so it can be cited later.",
  "Each tool has a Pydantic argument schema, a hard row cap, and normalises its results "
  "into evidence rows carrying source_table and source_pk.",
  ["backend/app/ai/tools.py", "backend/tests/unit/test_tools.py",
   "backend/tests/integration/test_tool_evidence.py"],
  ["every tool only issues SELECT statements (query-log assertion)",
   "results above the row cap are truncated deterministically",
   "each tool call can produce a citable evidence row with source_table and source_pk"])

t(29, "Bounded agent loop", "5 - AI layer", "2.0 days", ["TICKET-028"],
  "Implement the plan, gather, hypothesise, test, conclude loop with budgets.",
  "The AI investigator works in a loop with a strict spending limit on tool calls and "
  "tokens, and every step is written down. An investigation that cannot finish does not "
  "run forever - it stops and says so.",
  "Persists every step into agent_trace_step and manages the investigation_run "
  "lifecycle with a terminal_reason.",
  ["backend/app/ai/agent_loop.py", "backend/tests/unit/test_agent_loop.py"],
  ["a scripted mock that never concludes terminates at budget_exhausted",
   "every step is persisted with an incrementing step_index",
   "the loop never exceeds the configured tool-call budget",
   "the loop makes no writes to source tables"])

t(30, "Verifier", "5 - AI layer", "2.0 days", ["TICKET-029", "TICKET-026"],
  "Re-check every numeric claim in the agent's report against the database.",
  "The most important safety component in the whole system. After the AI writes its "
  "report, code goes through every number and checks it against the real records. "
  "Anything invented is dropped, and the case is downgraded to needs-review.",
  "Re-fetches every cited evidence source, validates every numeric claim, emits a "
  "verifier_report that drives the confidence gates.",
  ["backend/app/ai/verifier.py", "backend/tests/unit/test_verifier.py",
   "backend/tests/integration/test_verifier_grounding.py"],
  ["a report with a fabricated amount is rejected and caps confidence at 60",
   "a report citing a non-existent evidence row fails",
   "a fully grounded report passes",
   "the verifier is deterministic given the same database state"])

t(31, "Report and recommendation generation", "5 - AI layer", "1.5 day", ["TICKET-030"],
  "Produce the investigation report and the correction proposal.",
  "Write the human-readable case file: what happened, why, what it is worth, what "
  "Finance should do - with a citation on every claim.",
  "The report schema deliberately has no numeric fields for the LLM to fill in. The "
  "model supplies narrative plus one qualitative factor (contract_clarity). The "
  "recommendation always carries requires_human_approval = true.",
  ["backend/app/ai/report.py", "backend/app/ai/prompts/investigate.md",
   "backend/tests/unit/test_report.py"],
  ["the report schema rejects any numeric field emitted by the LLM",
   "exactly one qualitative factor is accepted",
   "the recommendation is never auto-approved",
   "the narrative contains inline citation markers that resolve to evidence rows"])

t(32, "Postgres job queue and worker loop", "5 - AI layer", "1.5 day", ["TICKET-006", "TICKET-029"],
  "A durable job table and worker process for background reconciliation and investigation.",
  "Long investigations run in the background so the website stays fast. Uses a table in "
  "Postgres rather than adding Redis or Celery - one less piece of infrastructure to run.",
  "FOR UPDATE SKIP LOCKED claiming, exponential backoff, max attempts, dead-lettering.",
  ["backend/app/jobs/queue.py", "backend/app/jobs/worker.py",
   "backend/tests/integration/test_job_queue.py"],
  ["two workers concurrently claim distinct jobs with no double-processing",
   "a failing job retries then dead-letters after max_attempts",
   "a graceful shutdown releases the lock",
   "a worker restart resumes queued jobs"])

# ---------------------------------------------------------------- Phase 6
t(33, "CUAD downloader, cache, offline fixture and licence notice", "6 - RAG and real data",
  "1.5 day", ["TICKET-003"],
  "Fetch the public CUAD contract dataset, cache it safely, and record its licence.",
  "Bring in real contracts written by real lawyers so we are testing against genuine "
  "messy legal prose rather than text we invented. The files are cached outside the "
  "repo and never committed, because the dataset licence is not clearly published.",
  "Verifies the archive hash against the known md5. Supports CUAD_OFFLINE=1 via a small "
  "committed fixture so tests never need the network. Writes THIRD_PARTY_NOTICES.md.",
  ["scripts/fetch_cuad.py", "backend/app/rag/cuad_adapter.py",
   "fixtures/cuad_sample.json", "THIRD_PARTY_NOTICES.md"],
  ["CUAD_OFFLINE=1 succeeds with zero network and returns 3 contracts",
   "a corrupted cache (bad hash) triggers a re-download",
   "contract text is never written into the repo tree",
   "the licence string is recorded, and the script fails loudly if it cannot be determined"])

t(34, "CUAD mapping, clause chunking and indexes", "6 - RAG and real data", "1.5 day",
  ["TICKET-033", "TICKET-006"],
  "Attach real contracts to synthetic customers, split into clauses, embed and index.",
  "Give each fake customer a real contract to search. The contract is chopped into "
  "individual clauses (not arbitrary blocks) so a citation can point at a precise "
  "sentence rather than 'page 4 somewhere'.",
  "Subset selection is deterministic (sorted hash, no randomness). Every clause gets an "
  "embedding and a full-text vector. Real company names must never reach customer rows.",
  ["backend/app/rag/chunking.py", "backend/app/rag/embeddings.py",
   "backend/app/rag/cuad_mapper.py", "backend/tests/integration/test_cuad_mapping.py"],
  ["selection is byte-identical across two runs",
   "every contract_clause has a non-null embedding and tsv",
   "no real company name appears in any customer row (asserted)"])

t(35, "Hybrid retrieval with reciprocal rank fusion", "6 - RAG and real data", "1.0 day",
  ["TICKET-034"],
  "Combine semantic vector search with keyword search and fuse the rankings.",
  "Search contracts two ways at once - by meaning and by exact words - then merge the "
  "two result lists. Meaning alone misses exact terms; keywords alone miss paraphrases. "
  "Together they are much better than either.",
  "pgvector semantic search plus Postgres full-text search, combined with reciprocal "
  "rank fusion.",
  ["backend/app/rag/retrieval.py", "backend/tests/integration/test_retrieval.py"],
  ["a query with a distinctive clause phrase returns the correct clause in the top 3",
   "both the lexical-only and semantic-only paths are exercised by tests",
   "RRF ordering is deterministic"])

t(36, "Clause extraction and evaluation harness", "6 - RAG and real data", "2.0 days",
  ["TICKET-035", "TICKET-027"],
  "Extract structured commercial terms from contracts and score accuracy against ~30 "
  "labelled clauses.",
  "Pull the actionable numbers out of legal prose - quantity, price, dates, effective "
  "period - then grade ourselves against a frozen set of about 30 clauses where we know "
  "the right answer.",
  "Includes negative items where the correct behaviour is to abstain rather than guess. "
  "Correctness is exact match or token-F1 above 0.9, plus a grounding check that the "
  "extracted text actually exists in the source.",
  ["backend/app/rag/clause_extraction.py", "backend/app/eval/suites/clause_extraction.py",
   "fixtures/golden/clauses.json", "backend/tests/integration/test_clause_eval.py"],
  ["per-field metrics are emitted",
   "grounding rate is 1.0 for the scripted mock (no fabricated spans)",
   "abstention on the negative items is scored as correct",
   "the test set hash matches the frozen value"])

# ---------------------------------------------------------------- Phase 7
t(37, "FastAPI skeleton, seeded roles and error model", "7 - API", "1.0 day", ["TICKET-006"],
  "Application factory, OpenAPI, uniform error responses, pagination and seeded roles.",
  "Stand up the web API with predictable error messages and three pretend user types "
  "(viewer, analyst, approver). This is explicitly not real login - it exists so the "
  "demo can show that only an approver can approve.",
  "A seeded-role dependency driven by a header. Explicitly out of scope: real "
  "authentication, multi-tenancy.",
  ["backend/app/api/main.py", "backend/app/api/deps.py", "backend/app/api/errors.py",
   "backend/tests/integration/test_api_skeleton.py"],
  ["/openapi.json validates",
   "every error response matches the documented envelope",
   "an approve endpoint called as viewer returns 403",
   "unknown roles are rejected"])

t(38, "Cases API", "7 - API", "1.5 day", ["TICKET-037", "TICKET-022"],
  "List and detail endpoints for investigation cases plus the change timeline.",
  "Let the website read cases: filter by status, customer, confidence band and date, "
  "and fetch the full detail including evidence and the change history.",
  "Filters compose. Detail returns the case, its periods, evidence, report, "
  "recommendation and agent trace.",
  ["backend/app/api/routers/cases.py", "backend/tests/integration/test_cases_api.py"],
  ["filters compose correctly and are covered by tests",
   "detail returns the full evidence chain with resolvable citations",
   "list is paginated with a stable sort",
   "a case with 5 affected periods returns one row with the correct range"])

t(39, "Decision API", "7 - API", "1.0 day", ["TICKET-038", "TICKET-023"],
  "Approve and reject endpoints that record outcomes and drive the state machine.",
  "Where a human says yes or no. Approving is deliberately idempotent - clicking twice "
  "must not double-count recovered money.",
  "Only operable on CONFIRMED_FOR_REVIEW or NEEDS_REVIEW cases. Records case_outcome "
  "and writes an audit event.",
  ["backend/app/api/routers/decisions.py",
   "backend/tests/integration/test_decisions_api.py"],
  ["approving an already-approved case is a no-op and returns 200",
   "rejecting requires a reason code",
   "a viewer cannot approve",
   "approving writes one audit_event and one case_outcome",
   "the recovered amount appears in the ledger query"])

t(40, "Ops API and constrained Q&A endpoint", "7 - API", "2.0 days", ["TICKET-037", "TICKET-030"],
  "Trigger runs, expose status, and implement 'ask the investigator' grounded in one case.",
  "Buttons to start a detection or investigation run, plus a question box that is "
  "strictly limited to the evidence in a single case. If the answer is not in that "
  "evidence, it refuses rather than making something up.",
  "Q&A is scoped to one case's evidence pack, returns citations that resolve to evidence "
  "rows, and returns refused=true when unsupported.",
  ["backend/app/api/routers/ops.py", "backend/app/api/routers/qa.py",
   "backend/app/ai/qa.py", "backend/tests/integration/test_qa_grounding.py"],
  ["an answerable question returns citations that resolve to evidence rows",
   "an unanswerable question returns refused=true with zero fabricated citations",
   "Q&A cannot access another case's evidence (scoping test)",
   "triggering a reconcile twice is idempotent"])

# ---------------------------------------------------------------- Phase 8
t(41, "Next.js scaffold, API client and role switcher", "8 - Frontend", "1.0 day", ["TICKET-037"],
  "App Router, Tailwind, shadcn/ui, a typed API client and a role switcher.",
  "The website shell and a way to switch between the pretend user types so the demo can "
  "show permissions working.",
  "The API client is typed against the generated OpenAPI schema - no `any`.",
  ["frontend/app/layout.tsx", "frontend/lib/api.ts", "frontend/components/role-switcher.tsx"],
  ["`next build` succeeds",
   "the client is typed against the OpenAPI schema",
   "switching roles visibly changes available actions",
   "zero `any` types in lib/api.ts"])

t(42, "Case queue UI", "8 - Frontend", "1.5 day", ["TICKET-041", "TICKET-038"],
  "The main working screen: a filterable table of investigation cases.",
  "The screen Finance lives in. Filters that stick in the URL, clear badges for severity "
  "and confidence, and one row per ongoing problem rather than one per month.",
  "Filters map directly to API parameters and persist in the URL. Empty, loading and "
  "error states are all designed.",
  ["frontend/app/cases/page.tsx", "frontend/components/case-table.tsx"],
  ["filters map to API params and are URL-persisted",
   "a 5-period case renders as one row showing the range",
   "empty, loading and error states are covered"])

t(43, "Case detail UI", "8 - Frontend", "2.0 days", ["TICKET-042", "TICKET-039"],
  "The single most important screen: chain of evidence, report, trace and decision panel.",
  "Where a human decides. Shows the contract-to-mismatch chain visually, every piece of "
  "evidence with a clickable excerpt, the AI's step-by-step trace, and approve or reject "
  "with a confirmation step.",
  "Every citation renders an excerpt with its source label. Approve/reject round-trips "
  "to the API without a page reload. Viewers see disabled actions.",
  ["frontend/app/cases/[id]/page.tsx", "frontend/components/evidence-chain.tsx",
   "frontend/components/agent-trace.tsx", "frontend/components/decision-panel.tsx"],
  ["every citation renders an excerpt with its source label",
   "the trace shows phases and tool calls in order",
   "approve/reject round-trips to the API and updates the badge without a reload",
   "a viewer sees disabled actions"])

t(44, "Change timeline, recovered-revenue ledger and time-to-detect simulator",
  "8 - Frontend", "2.0 days", ["TICKET-042", "TICKET-040"],
  "Three supporting views: what changed, what we recovered, and what faster detection "
  "would have saved.",
  "The 'what changed' view turns a mismatch into a story with dates. The ledger tracks "
  "money actually recovered. The simulator answers 'if we had caught this in month one, "
  "how much would we have saved?' - a strong closing beat for a demo.",
  "Timeline groups events by system with old to new values. Ledger totals must reconcile "
  "to the case_outcome sums. Simulator persists its run configuration.",
  ["frontend/app/timeline/page.tsx", "frontend/app/ledger/page.tsx",
   "frontend/app/simulator/page.tsx"],
  ["the timeline groups events by system with correct old to new values",
   "the ledger totals recovered vs written-off vs open and reconciles to case_outcome sums",
   "re-running the simulator with different parameters produces a different distribution"])

# ---------------------------------------------------------------- Phase 9
t(45, "Golden evaluation harness", "9 - Evaluation", "2.0 days",
  # TICKET-019 is detectors batch 2 (the last detection work this depends on).
  ["TICKET-019", "TICKET-025", "TICKET-026"],
  "Score detection precision and recall, exception classification and confidence calibration.",
  "The report card. Because the fake data was generated from recipes, we know every "
  "right answer - so we can measure exactly how often the system is right, how often it "
  "cries wolf, and whether its confidence scores actually mean anything.",
  "Writes metrics to eval_run and eval_result, reproducible from git_sha plus "
  "dataset_version.",
  ["backend/app/eval/harness.py", "backend/app/eval/suites/detection.py",
   "backend/app/eval/suites/exceptions.py", "backend/app/eval/suites/calibration.py",
   "backend/tests/integration/test_eval_harness.py"],
  ["on the seeded golden set, detection recall is at least 0.95",
   "detection precision is at least 0.90",
   "every legitimate exception is classified as VALID_EXCEPTION with zero false leakage cases",
   "metrics are written to eval_run and eval_result and are reproducible"])

t(46, "End-to-end pipeline test and property suite", "9 - Evaluation", "2.0 days",
  ["TICKET-040", "TICKET-045"],
  "A full run from empty database to approved case, plus consolidated invariant tests.",
  "One test that does the whole journey end to end with no network: generate data, "
  "detect, investigate, approve, check the ledger. Proves the pieces actually fit "
  "together, not just that each works alone.",
  "Plus the consolidated Hypothesis suite covering interval additivity, money "
  "conservation and confidence determinism.",
  ["backend/tests/e2e/test_full_pipeline.py", "backend/tests/property/test_invariants.py"],
  ["the e2e test passes with zero network access",
   "the e2e test asserts one case per injected leak with correct amounts",
   "property tests cover interval additivity, money conservation and confidence determinism",
   "the suite runs within the CI timeout"])

t(48, "Managed-RAG comparison baseline (Cloudflare AI Search)", "9 - Evaluation", "1.0 day",
  ["TICKET-035", "TICKET-045"],
  "Optionally benchmark our own retrieval against Cloudflare AI Search and record the result.",
  "A 'how do we know ours is any good?' check. We point the same questions at a paid "
  "managed search service and compare. This is for measurement only - the product itself "
  "keeps using the pipeline we built.",
  "Deliberately optional and skipped when credentials are absent. Exists to demonstrate "
  "engineering judgement: we considered the managed option, measured it, and documented "
  "why we kept our own. See docs/adr/ADR-009-cloudflare-ai-search.md.",
  ["backend/app/eval/suites/managed_baseline.py", "docs/adr/ADR-009-cloudflare-ai-search.md"],
  ["with no credentials configured the suite skips cleanly and still passes",
   "the same frozen 30-clause set is used for both sides of the comparison",
   "results are recorded with a note that no managed service is used in the product path",
   "no application code path depends on this suite"])

t(47, "Documentation, ADRs, licence notices and runbook", "9 - Evaluation", "1.5 day",
  ["TICKET-046"],
  "Finish the README, architecture diagram, decision records and operational runbook.",
  "Write it all up: how to start the project, why each big decision was made, and what "
  "to do when things break. Also confirms the third-party licence handling.",
  "Every locked decision gets an ADR stating its reason. The runbook lists the most "
  "common failures with fixes.",
  ["README.md", "docs/architecture.md", "docs/adr/ADR-*.md", "docs/runbook.md",
   "THIRD_PARTY_NOTICES.md"],
  ["a fresh clone reaches a seeded running app following only the README",
   "every locked decision has an ADR stating its reason",
   "the CUAD licence and non-redistribution policy are documented",
   "the runbook lists the top 5 failure modes with remediation"])

# Added after auditing the ticket set against the original 41-section spec.
t(49, "Ingestion layer", "2 - Data generation", "1.5 day",
  ["TICKET-005", "TICKET-006"],
  "Load business records into the source tables from files and documents, validating "
  "and normalising them on the way in.",
  "Everything has to get into the system somehow. This builds the front door: it takes "
  "a CSV of invoices, a JSON export from the CRM, or a folder of contract documents, "
  "checks each one is shaped correctly, converts dates and currencies into one "
  "consistent format, and files it away with a note recording where it came from. The "
  "important idea is traceability - later we point at these rows as evidence, and if we "
  "lose the origin the evidence is worthless.",
  "The architecture shows an INGEST stage between the data sources and the canonical "
  "model. TICKET-033 and TICKET-034 handle CUAD contract documents specifically; this "
  "is the general machinery everything else uses. Every ingested row carries "
  "source_system and source_id. Nothing is silently dropped - a malformed record is "
  "logged as an ingestion error and skipped, not crashed on. Ingestion is idempotent "
  "because (source_system, source_id) is a natural key enforced by the schema.",
  ["backend/app/ingest/base.py", "backend/app/ingest/tabular.py",
   "backend/app/ingest/documents.py", "backend/app/ingest/validate.py",
   "backend/app/ingest/normalize.py", "backend/tests/unit/test_ingest_validate.py",
   "backend/tests/integration/test_ingest_idempotency.py"],
  ["a CSV and a JSON payload both load into the source tables",
   "every ingested row carries source_system and source_id",
   "a schema violation raises an error naming the field and the row number",
   "timestamps are normalised to UTC and currencies to ISO 4217 codes",
   "loading the same payload twice leaves row counts unchanged",
   "a malformed record is logged as an ingestion error and skipped, not fatal",
   "a test asserts no row exists without a source_system value"])

t(50, "Anomaly detectors", "3 - Deterministic core", "1.5 day",
  ["TICKET-016", "TICKET-024"],
  "Add trend, ratio and historical-comparison detectors alongside the rule-based ones.",
  "The rule-based detectors catch problems we already know the shape of, like contract "
  "says 100 and billing says 70. These catch problems nobody wrote a rule for: revenue "
  "that suddenly drops, usage that keeps climbing while billing stays flat, or the same "
  "discrepancy reappearing every month. They run alongside the rules, not instead.",
  "Three detector families, all statistical rather than model-based: trend "
  "(month-over-month revenue change beyond a threshold), ratio (usage-to-billing ratio "
  "drifting outside a band), and historical (the same discrepancy recurring across "
  "consecutive periods). Every alert must record which detector produced it - the "
  "product says 'detected by the usage/billing ratio detector', never 'the AI noticed "
  "something'. Deliberately not using Isolation Forest: at 50-100 customers simple "
  "statistics are more accurate and, critically, explainable to a Finance user.",
  ["backend/app/detect/anomaly/trend.py", "backend/app/detect/anomaly/ratio.py",
   "backend/app/detect/anomaly/historical.py",
   "backend/tests/unit/test_anomaly_detectors.py",
   "backend/tests/integration/test_anomaly_attribution.py"],
  ["a sudden month-over-month revenue drop is detected",
   "a usage-to-billing ratio breach is detected",
   "a discrepancy recurring across consecutive periods is detected",
   "every alert records its detector_id - an alert with no attribution fails the test",
   "thresholds are read from configuration, not hardcoded",
   "zero alerts on 100 clean generated customers"])

t(51, "Overview dashboard and analytics", "8 - Frontend", "2.0 days",
  ["TICKET-041", "TICKET-038", "TICKET-040"],
  "Build the landing screen and the analytics screen.",
  "This is the first screen anyone sees, including in the demo video. Four headline "
  "numbers at the top - money at risk, confirmed, recovered, and how many cases are "
  "waiting - then charts answering where the money is leaking and why. Read "
  "docs/ux-ui-plan.md first: it defines the visual language, the exact wording for "
  "every label, and the layout. This ticket implements it.",
  "Top cards: potential leakage, confirmed leakage, recovered revenue, open "
  "investigations. Then leakage trend over time, leakage by root cause, by product, by "
  "customer, high-risk accounts, and detection performance. No chart may exist without "
  "answering a business question - if you cannot state the question in one sentence, "
  "delete the chart. All numbers come from the API; nothing is hardcoded.",
  ["frontend/app/page.tsx", "frontend/app/analytics/page.tsx",
   "frontend/components/metric-card.tsx",
   "frontend/components/leakage-trend-chart.tsx",
   "frontend/components/breakdown-chart.tsx",
   "frontend/components/high-risk-accounts.tsx"],
  ["the four headline cards render values from the API",
   "a leakage trend chart renders across the 12-month dataset",
   "breakdowns render by root cause, product and customer",
   "a high-risk accounts list renders, sorted by exposure",
   "every number traces to an API response - no hardcoded figures anywhere",
   "each chart has a one-sentence business question stated in the code as a comment",
   "loading, empty and error states are all designed"])

# Title kept short so the generated filename matches the committed one exactly.
# Do not rename without also renaming docs/tickets/TICKET-052-* and its README link.
t(52, "Customer risk view and integrity score", "8 - Frontend", "1.5 day",
  ["TICKET-038", "TICKET-026"],
  "A per-customer screen showing revenue health, plus the computed Revenue Integrity Score.",
  "One page per customer answering: how much are they supposed to be paying, how much "
  "are we actually invoicing, how big is the gap, and how much can we trust their data? "
  "The score is a 0-100 operational hint, not a financial statement, and must be "
  "labelled as internal and non-authoritative everywhere it appears. Read "
  "docs/ux-ui-plan.md for the layout and the exact wording to use.",
  "Per customer: current ARR, contracted ARR, billed ARR, potential leakage, leakage "
  "percentage, open cases, historical cases, products, contracts, billing health. The "
  "score breaks into five labelled components so a user can see why it is low: contract "
  "integrity, billing integrity, usage alignment, data completeness, open exceptions. "
  "The score is deterministic and computed in code; the AI contributes nothing to it.",
  ["frontend/app/customers/[id]/page.tsx", "frontend/components/integrity-score.tsx",
   "backend/app/cases/integrity_score.py",
   "backend/tests/unit/test_integrity_score.py"],
  ["the page shows current, contracted and billed ARR side by side",
   "the score renders with all five component breakdowns visible",
   "the score is labelled an internal operational metric, not an audited figure",
   "the score is deterministic - identical inputs give identical output",
   "the score is computed without any LLM call",
   "open and historical cases are listed for the customer"])

# ---------------------------------------------------------------- render
os.makedirs(OUT, exist_ok=True)

for x in sorted(T, key=lambda d: d["num"]):
    num = f"TICKET-{x['num']:03d}"
    deps = ", ".join(x["deps"]) if x["deps"] else "none"
    lines = []
    lines.append(f"# {num} - {x['title']}")
    lines.append("")
    lines.append(f"- **Status:** TODO")
    lines.append(f"- **Phase:** {x['phase']}")
    lines.append(f"- **Effort:** {x['effort']}")
    lines.append(f"- **Depends on:** {deps}")
    lines.append("")
    lines.append("## Goal")
    lines.append("")
    lines.append(x["goal"])
    lines.append("")
    lines.append("## What this means")
    lines.append("")
    lines.append(x["plain"])
    lines.append("")
    lines.append("## Context")
    lines.append("")
    lines.append(x["context"])
    lines.append("")
    lines.append("## Deliverables")
    lines.append("")
    for d in x["deliverables"]:
        lines.append(f"- `{d}`")
    lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("")
    for c in x["criteria"]:
        lines.append(f"- [ ] {c}")
    if x["notes"]:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        for n in x["notes"]:
            lines.append(f"- {n}")
    lines.append("")
    lines.append("## Definition of done")
    lines.append("")
    lines.append("- [ ] every deliverable file exists")
    lines.append("- [ ] every acceptance criterion above is checked off")
    lines.append("- [ ] `make test` passes")
    lines.append("- [ ] no rule in `AGENTS.md` was violated")
    lines.append("- [ ] status updated to DONE and committed with the co-author trailer")
    lines.append("")

    slug = (x["title"].lower().replace(",", "").replace("(", "").replace(")", "")
            .replace("/", "-").replace(" ", "-").replace("--", "-"))
    slug = "".join(ch for ch in slug if ch.isalnum() or ch == "-").strip("-")[:52]
    path = os.path.join(OUT, f"{num}-{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

print(f"wrote {len(T)} ticket files")
