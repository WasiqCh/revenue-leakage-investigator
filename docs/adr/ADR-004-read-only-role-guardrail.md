# ADR-004: The read-only database role is the guardrail, not the prompt

**Status:** Accepted — 2026-09-21

## What this means

The product's central promise is that the AI never changes an invoice. We enforce that with a **database permission**, not an instruction in the AI's prompt. When the investigating agent talks to the database it logs in as a user called `rl_readonly` that has been granted only `SELECT` — the ability to read rows and nothing else. It physically cannot update, insert or delete; the database refuses before any application code is consulted. A **prompt** is the text we send telling the AI what to do, and prompts can be argued with, forgotten or overridden by clever input. A permission cannot. We also install **triggers** — code the database runs automatically on certain events — that block any update or delete on `audit_event` and `agent_trace_step`, so the record of what the system did is append-only: rows can be added, never rewritten.

## Context

Prompt-based guardrails are the default industry practice and they are not guardrails. The model is asked not to write to billing, then a retrieved contract clause reads like an instruction and the model complies. That is **prompt injection**: untrusted content arriving through a legitimate channel being treated as a command. Our agent reads contract prose from an external dataset, so untrusted text is the normal input, not an edge case. Two further problems. A promise that lives in a prompt cannot be tested — you cannot write an assertion that a model will never do something. And "we asked the AI not to" is not an answer a Finance or security reviewer accepts. If an audit row can be edited, the audit trail proves nothing, including about us.

## Decision

**The agent connects to Postgres as `rl_readonly`, a `SELECT`-only role. Every agent tool is declared read-only and enforced by test. `audit_event` and `agent_trace_step` carry `BEFORE UPDATE OR DELETE` triggers that raise an exception, making them effectively append-only.**

- The application role, used by the API and worker, is separate from `rl_readonly`, and only it may write to `case`, `evidence`, `recommendation`, `investigation_report`, `agent_trace_step`, `audit_event`, `case_outcome` and `job`.
- The agent process never holds the application role's credentials.
- Each tool in `backend/app/ai/tools.py` carries `read_only=True`; a test fails the build if one is added without it or mutates a `source_*` table.
- An acceptance test attempts a write as `rl_readonly` and asserts the database refuses it.
- Retention on the audit tables uses partition drops, never `DELETE`.

## Alternatives considered

- **A prompt instruction never to modify billing data.** Rejected. Unenforceable, untestable, defeated by any retrieved text that looks like an instruction, and a claim rather than a control.
- **Application-level checks that reject mutating SQL.** Rejected as the primary control. Good defence in depth, but it lives in the same process as the agent, so a bug or a refactor can remove it. The database grant lives outside the blast radius.
- **A read replica for the agent.** Rejected as the guardrail. It is a performance and isolation pattern, not a permission, and it doubles the infrastructure that ADR-002 and ADR-005 are both trying to avoid. Plausible later for load reasons only.
- **Soft deletes and version rows instead of triggers.** Rejected for the audit tables specifically. Soft deletes leave the original row mutable, which is the thing we are trying to prevent.
- **Writing audit rows to an external append-only log.** Rejected. It adds a service, breaks the single-datastore story, and makes the trace harder to join against cases for the UI.

## Consequences

**Easier.** The headline claim becomes a testable, demonstrable fact rather than a policy. Prompt injection loses its worst outcome: the agent can be manipulated into saying something wrong, and never into changing a number. The audit trail is trustworthy because it is structurally immutable. Reviewers get a one-line answer.

**Harder.** Correcting a case must go through the application role and a deliberate code path, which is more plumbing than letting the agent "just fix it". Append-only triggers mean mistakes in the trace stay in the trace — correct, but occasionally inconvenient — and retention must use partition drops rather than deletes.

**Negative.** Two credentials to manage and rotate instead of one, plus a migration granting and revoking roles that must be kept in step with the application's expectations. If the role is misconfigured in a new environment the agent fails closed: investigations error rather than run. That is the right failure direction, but it will look like a bug to whoever deploys it first.

## How to reverse it

Granting the agent write access means dropping the `rl_readonly` separation, removing the append-only triggers, and deleting the tests that assert writes are refused — after which the product can no longer claim the AI is structurally incapable of mutating financial data, and the README's credibility section becomes false.
