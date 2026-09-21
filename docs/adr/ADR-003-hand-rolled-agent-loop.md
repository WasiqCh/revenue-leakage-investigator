# ADR-003: A hand-rolled agent loop, not an agent framework

**Status:** Accepted — 2026-09-21

## What this means

An **agent** is an AI that does not answer once — it works in steps, calling tools and reading results before deciding what to do next. A **framework** is a large off-the-shelf library that supplies that stepping behaviour for you. We are not using one. We wrote the loop ourselves in a few hundred lines of Python: the model plans what it needs, gathers data through tools, forms a hypothesis, tests it and concludes. The loop has hard limits — a maximum number of tool calls and a maximum number of **tokens** (units of text the model reads and writes) — so a confused agent stops and escalates instead of burning money forever. Because we wrote it, every step is recorded in our own `agent_trace_step` table in our own format, and the loop is testable without calling a real model.

## Context

Agent frameworks are genuinely useful for prototyping, and the temptation was strong. We rejected them for four reasons. The trace is a deliverable: the product claims a reviewer can see *why* the system believes there is leakage, so the trace is user-facing evidence needing a stable, versioned shape — and framework traces are the framework's shape. Framework churn is real: this codebase has 48 tickets and a long life, and a dependency whose interfaces move turns maintenance into rewrites. Tests must run offline with `LLM_MOCK=1`, which is trivial when we own the loop and becomes an integration test when we do not. And tool-call and token budgets must be exact, which is awkward through someone else's callback system.

## Decision

**We implement the agent loop ourselves in `backend/app/ai/agent_loop.py` with five explicit phases — Plan, Gather, Hypothesize, Test, Conclude — and enforce tool-call and token budgets per investigation. We add no agent framework.**

- The loop reaches the model only through `backend/app/ai/provider.py`, the single seam where a real provider or the mock is injected.
- Every phase transition and tool call writes an `agent_trace_step` row with tool name, arguments, result digest, token counts and elapsed time.
- Budgets are configuration, not constants. Exceeding one ends the investigation and sets the case to `NEEDS_REVIEW` with an explicit reason.
- Tools are declared read-only and validated against a Pydantic v2 schema before execution.
- Model output is constrained to text plus the single `contract_clarity` enum, per [ADR-001](ADR-001-deterministic-money-no-llm-math.md).

## Alternatives considered

- **LangChain.** Rejected. A very large dependency surface for the small part we would use, historically unstable across versions, and it puts logic in chains and prompt templates that our tests cannot reach.
- **LangGraph.** Rejected. The closest fit — an explicit graph of states is roughly our five phases — but still an external definition of our loop, and its persistence duplicates the trace table the UI already needs.
- **PydanticAI.** Rejected, and the closest call. We use Pydantic v2 everywhere so it would fit naturally, but the loop is small enough that its added value is low and the cost is the exact trace format the product is selling.
- **LlamaIndex.** Rejected. Optimised for retrieval and indexing; the agent side is the weaker half and we already own the retrieval design.
- **CrewAI.** Rejected. Multi-agent role-play with no fit here — we have one investigator, not a crew, and more agents means more failure modes without more capability.

## Consequences

**Easier.** The trace is ours: we define, version and render it without translation. Tests are fast, offline and deterministic because we inject a mock provider. Budgets are exact and auditable. A model or SDK upgrade touches one file, and no framework release can break the product.

**Harder.** We reimplement retry with backoff, provider-specific tool-call formatting, streaming and prompt caching. When a model ships a novel calling convention, we adapt it ourselves. A new engineer will not recognise our loop from prior experience and must read it.

**Negative.** The first version will be less robust than a mature framework. We will discover edge cases — tool-call truncation, malformed JSON, provider rate limits — the hard way, in production-shaped conditions rather than in a library that has already met them.

## How to reverse it

Adopting a framework later means porting the five phases into its graph or chain model, re-implementing the trace adapter against its callbacks, and rewriting the offline tests. The tools and the provider seam survive unchanged, so the blast radius stays inside `backend/app/ai/`.
