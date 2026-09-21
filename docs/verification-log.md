# Verification log

Chronological record of every verification run. This is the evidence; the
scoreboard in [`tickets/VERIFICATION.md`](tickets/VERIFICATION.md) is the status.

One entry per check. Nothing is deleted or rewritten — append only.

---

## Entry template

```markdown
### 2026-00-00 — G0 / TICKET-000

- **Scope:** gate G0, tickets 001–005 (or: individual check on TICKET-008)
- **Commit:** `abc1234` → `def5678`
- **Tier 1 (static):** ran `python scripts/verify_ticket.py 001 002 003 004 005`
- **Tier 2 (Docker):** `make verify` evidence attached — yes / no

#### Findings

| Severity | Issue | Location | Disposition |
|---|---|---|---|
| SEV1 | example | `path:line` | fixed in `abc1234` / open |

#### Tier 2 evidence

```
paste the relevant part of artifacts/verify-report.md here
tests collected: N
```

#### Verdict

**PASS / FAIL / BLOCKED / NEEDS EVIDENCE** — one-line reason.

#### Escalation

Only if SEV1: what was asked, and the decision.
```

---

## Rules

- **Any SEV1 stops the gate** and is escalated before work continues.
- Three or more SEV2s triggers a recommendation to stop.
- SEV3 and SEV4 never block; they are logged for later cleanup.
- A ticket that cannot be confirmed without Docker is **BLOCKED**, never PASS.
- The collected-test count must be recorded. A suite with zero tests is SEV1.

---

## Entries

_No verification runs recorded yet._
