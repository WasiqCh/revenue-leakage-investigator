# Demo script

A click-by-click script for recording the two-minute demo video.

Everything here is designed to be *watchable*. People will watch the recording
far more often than they will read the documentation, so the labels are plain,
the flow is linear, and every screen has one job.

---

## What this means

This demo proves three things in two minutes.

First, that the system finds a real, silent revenue leak that nobody inside the
company can currently see, because each team only looks at its own system.

Second, and more importantly, that it is *not* a dumb "the numbers differ,
therefore we are losing money" tool. It shows a legitimate exception being
correctly closed with zero AI investigation, an ambiguous case where the system
explicitly refuses to guess, and a false positive that was correctly suppressed.

Third, that money is computed by deterministic code and never by the AI, and that
a human in Finance is the only actor who can approve a correction.

If a viewer remembers one sentence, it should be: **AI is the investigator, code
is the accountant, the human is the judge.**

---

## Before you record

You need Docker running. There is no non-Docker path.

```bash
cp .env.example .env      # then fill in LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
make up                   # start database, API, worker, website
make seed                 # generate the synthetic company dataset
make reconcile            # run detection across all customers
make investigate          # run agent investigations on all open cases
open http://localhost:3000
```

Or, in one command:

```bash
make demo
```

**Before you hit record, check these:**

- `make up` has finished and the database health check is passing.
- `make demo` completed without errors in the terminal.
- The browser is at `http://localhost:3000/cases`.
- The role switcher (top right) is set to **Approver**.
- Zoom is at 110–125% so labels are readable in the recording.
- The browser has no other tabs visible, and notifications are silenced.

Total recording target: **2 minutes**.

---

## The flow at a glance

| Time | Screen | Route | One-line purpose |
|---|---|---|---|
| 0:00–0:15 | Case queue | `/cases` | Show the size of the problem |
| 0:15–0:50 | Hero case | `/cases/<acme-id>` | The Acme story, end to end |
| 0:50–1:10 | Evidence chain | same page, upper panel | Prove it with real records |
| 1:10–1:30 | Agent trace | same page, lower panel | Show the AI's work and its limits |
| 1:30–1:45 | Decision panel | same page, right rail | Show that only a human decides |
| 1:45–2:00 | Time-to-detect simulator | `/simulator` | The closing beat |

---

## Screen 1 — The case queue

**Route:** `/cases`

**What the viewer should see:** a filterable table with one row per ongoing
problem. The first row is the hero case.

**Exact labels to point at:**

| Column | Value on the hero row |
|---|---|
| Customer | `Acme Corporation` |
| Problem | `Seat underbilling` |
| Affected period | `2026-04-01 → 2026-08-31` |
| Potential leakage (monthly) | `$3,600.00` |
| Confidence | `94%` |
| Status badge | `Awaiting Finance Review` |

**What to say while recording:**

> "This is the queue Finance works from. One row per ongoing problem — not one row
> per month. Acme Corporation has been under-billed since April and nobody inside
> the company has noticed, because every team's own system looks fine."

**Notes for the recording:** the affected period shows a range rather than five
separate rows. That is deliberate — the same mismatch repeating for five months is
one case, and if it produced five rows the queue would become unusable.

---

## Screen 2 — The hero case

**Route:** `/cases/<acme-id>` (click the `Acme Corporation` row)

**What the viewer should see:** the case header, then the five-system comparison.

**Exact labels to point at — the five systems panel:**

| System | Label in the UI | Value shown |
|---|---|---|
| Contract | `Contract` | `100 Enterprise seats @ $120.00 / seat / month` |
| Contract | `Effective from` | `2026-04-01` |
| CRM | `CRM` | `100 seats sold` |
| Implementation | `Implementation` | `100 seats activated` |
| Product usage | `Usage` | `97 seats active` |
| Billing | `Billing` | `70 seats invoiced` |
| Exceptions | `Approved exceptions` | `None` |

**Exact labels to point at — the impact panel:**

| Label | Value |
|---|---|
| `Potential leakage — monthly` | `$3,600.00` |
| `Affected period` | `2026-04-01 → 2026-08-31 (5 periods)` |
| `Potential leakage — historical` | `$18,000.00` |
| `Root cause` | `Billing configuration not updated after amendment AM-1042` |
| `Confidence` | `94%` |
| `Status` | `Awaiting Finance Review` |

**What to say while recording:**

> "Five systems, five teams, five answers. Contract says 100 seats at a hundred
> and twenty dollars. CRM says 100 sold. Implementation says 100 activated.
> Usage says 97 people actually logged in. Billing invoices 70.
>
> Thirty seats are missing at a hundred and twenty dollars each — that's three
> thousand six hundred dollars a month. It has been running since April, so
> eighteen thousand dollars so far.
>
> And there is no approved exception on this account, so nothing here is
> intentional."

**Why 97 usage does not change the answer — say this if you have time:**

> "Usage says 97, not 70. But usage only tells us how many people logged in — it
> is not a billing basis. The contract is the billing basis. The gap we can prove
> is the one between the contract and the invoice: thirty seats."

---

## Screen 3 — The evidence chain

**Route:** same page, upper panel, labelled `Evidence chain`

**What the viewer should see:** the contract-to-mismatch chain drawn out, with
each step backed by a clickable excerpt from a real record.

**Exact labels to point at:**

| Step label | What it shows |
|---|---|
| `Contract` | The clause establishing 100 seats at $120.00 |
| `Amendment AM-1042` | The signed amendment that changed the deal |
| `CRM opportunity` | `100 seats sold` |
| `Implementation record` | `100 seats activated` |
| `Invoice line` | `70 seats invoiced` |
| `No approved exception` | The exception lookup returned nothing |

**What to say while recording:**

> "This is the chain. Every link is a real record with a real excerpt — click any
> of them and you see the actual text it came from. Nothing here is the AI's
> summary of the contract; it is the contract, quoted, with its source attached."

**If you click one excerpt, click the amendment.** It is the pivot of the whole
story: the deal changed, and billing was never told.

---

## Screen 4 — The agent trace

**Route:** same page, lower panel, labelled `Investigation trace`

**What the viewer should see:** the agent's steps in order — the phases it went
through and the tools it called — each with its result.

**Exact labels to point at:** `Plan`, `Gather evidence`, `Hypothesis`, `Test`,
`Conclude`, and the individual tool calls underneath each phase.

**What to say while recording:**

> "This is the AI investigator's actual work, step by step. It planned, it fetched
> the contract clauses, it fetched the amendment, it fetched the invoice lines,
> it formed a hypothesis, and it tested it.
>
> Notice what it did *not* do. It never did arithmetic. It never wrote to the
> database — it connects as a read-only database user, so writing is not something
> it is trusted not to do, it is something it is *unable* to do.
>
> And the confidence score you saw — ninety-four percent — was not produced by the
> model. It was computed by our own code from eight weighted factors. The model
> contributed exactly one of them: how clearly the contract was worded. A model
> telling you it feels ninety-four percent confident is worthless."

---

## Screen 5 — The decision panel

**Route:** same page, right rail, labelled `Decision`

**What the viewer should see:** the proposed correction, the amount, and
`Approve` / `Reject` / `Mark as legitimate exception` buttons.

**What to say while recording:**

> "The system proposes. It does not act. This correction cannot be applied without
> a human in Finance pressing Approve."

**Then demonstrate the permission boundary:**

1. Switch the role switcher (top right) from `Approver` to `Viewer`.
2. Point at the decision panel. The buttons are now disabled.
3. Switch back to `Approver`.

> "And it is not just a greyed-out button. The API itself refuses an approve
> request from a viewer role — you get a 403. The permission is enforced on the
> server, not hidden in the browser."

**Do not press Approve during the recording** unless you intend to show the
ledger afterwards, because it changes the state of the demo dataset. If you want
a clean re-run, `make seed` resets everything.

---

## The part that matters most: this is not "numbers differ, therefore leakage"

This is the section that separates the product from every naive spreadsheet
comparison. Walk through these three cases immediately after the hero case.

### Case A — A legitimate exception (zero AI investigation)

**Route:** `/cases`, filter by status `Valid exception`

**What the viewer should see:** a case with status badge `Valid exception`,
a reason of `Approved discount`, and an investigation panel reading
`No investigation required`.

**What to say while recording:**

> "This one looks identical to the Acme case. The numbers disagree. Billing is
> lower than the contract. A naive system would flag it.
>
> But there is an approved discount covering this exact customer and this exact
> period. So it closes as a valid exception — and note that the AI never ran.
> Zero investigations, zero tokens, zero cost. We only spend AI effort on things
> that are actually ambiguous."

### Case B — An ambiguous case (the system refuses to guess)

**Route:** `/cases`, filter by status `Needs review`

**What the viewer should see:** a case with status badge `Needs review`, a
confidence below the review threshold, and a report that states plainly that the
available records do not determine the answer.

**What to say while recording:**

> "Here the system genuinely cannot tell. The records are incomplete, and there is
> no way to establish from the data whether this is leakage or not.
>
> The correct answer is to say so and escalate — not to guess. This case is
> marked Needs review and left for a human. A system that always produces a
> confident answer is a system you cannot trust."

### Case C — A false positive that was correctly suppressed

**Route:** `/cases`, filter by status `Valid exception`, look for the
`Usage over-entitlement` entry

**What the viewer should see:** a case that was detected as a potential problem,
then correctly closed as not leakage, with the reason shown.

**What to say while recording:**

> "And this one was a genuine near-miss. The usage pattern tripped the
> over-entitlement rule, but the exception registry and the period logic both
> agreed it was within tolerance for this contract. It was suppressed rather than
> sent to Finance.
>
> That is the whole point. Precision matters more than volume. If Finance gets
> twenty rows and three of them are noise, they stop opening the queue — and then
> the real eighteen-thousand-dollar problem sits there unread."

---

## The closing beat: the time-to-detect simulator

**Route:** `/simulator`

**What the viewer should see:** a control for "detect in month N" and a resulting
savings figure.

**Set the detection month to month 1.**

**Exact labels to point at:**

| Label | Value |
|---|---|
| `Detected in month` | `1` |
| `Actually detected in month` | `5` |
| `Avoided leakage` | `$14,400.00` |
| `Actual leakage` | `$18,000.00` |

**What to say while recording:**

> "One more number. If we had caught this in month one instead of month five, we
> would have saved fourteen thousand four hundred dollars on this single
> customer.
>
> That is the real argument. Not 'the AI found a mismatch' — but 'this system
> pays for itself by closing the gap between when a problem starts and when
> somebody notices'."

**Stop recording here.**

---

## Which scenarios are fully agent-investigated

Be precise about this if anyone asks, because it is a deliberate design choice
and not a limitation.

The demo dataset contains **10 leakage patterns plus a set of legitimate
exceptions**.

- **5 scenarios run the full agent investigation end-to-end**, with a real trace,
  real tool calls and a verifier pass:
  1. real leakage (the Acme seat-underbilling hero case)
  2. legitimate exception
  3. ambiguous case
  4. duplicate customer
  5. missing evidence
- **The remaining 5 are rule-detected**, producing a deterministic explanation
  rather than an AI investigation.

**Why:** a live model call per case would make the demo slow, non-deterministic
and dependent on a network. Rule-detected cases are instant and identical on
every machine, so the demo always runs in the same two minutes. The agent path is
still exercised end to end — it is simply reserved for the cases where
investigation actually adds something.

Say it like this:

> "Five of these go through the full AI investigation. The other five are caught
> by deterministic rules with a written explanation. That is on purpose — there
> is no reason to spend a model call on a case where a rule already knows the
> answer, and it keeps the demo fast and repeatable."

---

## Resetting between takes

```bash
make seed        # regenerates the dataset and clears prior cases
make reconcile   # re-run detection
make investigate # re-run the agent investigations
```

`make seed` is idempotent — running it twice with the same seed produces
byte-identical output, so take two looks exactly like take one.

---

## Common recording problems

| Symptom | Fix |
|---|---|
| Queue is empty | `make seed` then `make reconcile` |
| Cases show no investigation | `make investigate`, and check the worker container is running |
| Confidence shows `—` | The verifier has not run yet; wait for the worker, then refresh |
| Wrong role on screen | Use the role switcher, top right |
| Labels look cramped | Raise browser zoom to 110–125% |

---

## Where to go next

- What the product is: [../README.md](../README.md)
- What every term means: [glossary.md](glossary.md)
- How to run and repair it: [runbook.md](runbook.md)
