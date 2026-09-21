# Verification scoreboard

Status at a glance. Evidence lives in
[`../verification-log.md`](../verification-log.md); the rules live in
[`../verification-protocol.md`](../verification-protocol.md).

| Verdict | Meaning |
|---|---|
| PASS | Tier 1 clean and Tier 2 evidence attached |
| FAIL | SEV1 or repeated SEV2 — returned with file and line |
| BLOCKED | Needs a Docker run; no evidence yet |
| NEEDS EVIDENCE | Code looks right, nothing proves behaviour |

**No ticket is DONE until both tiers pass.**

---

## Gates

| Gate | After | Must be true | Verdict | Date | Commit | SEV1/2/3 |
|---|---|---|---|---|---|---|
| G1 | 005 | Stack boots, migrations apply | — | — | — | — |
| G2 | 010 | Dataset generates deterministically | — | — | — | — |
| G3 | 015 | Expected revenue ignores invoices | — | — | — | — |
| G4 | 020 | Detection finds injected discrepancies | — | — | — | — |
| G5 | 025 | Cases dedupe, exceptions route | — | — | — | — |
| G6 | 030 | Agent investigates, verifier rejects | — | — | — | — |
| G7 | 035 | Clauses retrieved and cited | — | — | — | — |
| G8 | 040 | API works, permissions enforced | — | — | — | — |
| G9 | 045 | Interface usable, eval reports metrics | — | — | — | — |
| G10 | 050 | Green end to end | — | — | — | — |
| G11 | 052 | Final | — | — | — | — |

## Checked individually

These are verified the moment they finish — a batch gate never replaces them.

| Ticket | Why | Verdict | Date | Commit |
|---|---|---|---|---|
| [007](TICKET-007-read-only-role-and-immutability-guards.md) | Guardrail: agent must be read-only | — | — | — |
| [008](TICKET-008-money-and-interval-primitives.md) | Everything downstream depends on exact money | — | — | — |
| [015](TICKET-015-expected-revenue-engine.md) | Must never read invoice tables | — | — | — |
| [022](TICKET-022-case-fingerprinting-and-idempotent-upsert.md) | Prevents duplicate-case noise | — | — | — |
| [026](TICKET-026-confidence-engine.md) | Trust must be measured, not asserted | — | — | — |
| [030](TICKET-030-verifier.md) | Stops invented numbers reaching Finance | — | — | — |

---

## How to run a check

```bash
git pull
python scripts/verify_ticket.py 014          # Tier 1, no Docker needed
python scripts/verify_ticket.py --gate 3      # everything up to gate G3
python scripts/verify_ticket.py --all         # full sweep
```

Then record the result here and append the detail to
[`../verification-log.md`](../verification-log.md).
