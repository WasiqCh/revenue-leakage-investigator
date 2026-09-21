# UI and UX plan

**Read this before building any screen.** It defines how the product looks, what
every label says, and how the screens fit together. The UI tickets
(TICKET-041 … 044, 051, 052) implement what is written here.

---

## What this means

This document decides what the product looks like and how a person moves through
it. The goal is narrow: **someone in Finance should be able to decide whether a
flagged revenue gap is real, in under a minute, without training.**

That is the only thing that matters. Anything that does not help that decision is
decoration and should be cut.

A secondary goal: the screens will be recorded for a demo video. So every label
must be self-explanatory — a viewer who has never seen the product should never
wonder what a thing is.

---

## 1. The one rule

**This must look like serious enterprise finance software. It must not look like an
AI demo.**

A Finance professional's first reaction to "AI" is suspicion. The interface has to
earn trust by being calm, precise and boring — then the intelligence shows through
in the *content*, not the styling.

| Do | Do not |
|---|---|
| Clean typography, generous spacing, clear hierarchy | Neon, glowing gradients, dark "hacker dashboard" |
| Subtle borders, professional tables, compact charts | Excessive gradients, glass effects, drop shadows everywhere |
| Status badges, evidence cards, timelines, side panels | Robot illustrations, generic AI icons, sparkles |
| Restrained colour used only for meaning | Colour used for decoration |
| Light, quiet surfaces | Chatbot as the main interface |

Reference point: Stripe's dashboard, or a modern revenue-operations tool. **Not** an
AI startup landing page.

---

## 2. Visual language

### Type
- One sans-serif family throughout
- Page title 24px · section heading 16px · body 14px · supporting text 13px
- Numbers use tabular figures so columns align
- Money is always right-aligned in tables

### Colour
Colour carries meaning only. Four semantic colours, plus neutrals:

| Meaning | Use |
|---|---|
| Neutral | Default surfaces, borders, body text |
| Warning | Potential leakage, open cases, medium confidence |
| Danger | Confirmed leakage, high severity, overdue |
| Success | Resolved, recovered revenue, valid exception |
| Info | Informational notes, low confidence |

Never use these colours decoratively. A red that means "severe" and a red that
means "a chart series" cannot coexist.

### Spacing and layout
- 8px base unit; 16/24/32px for section rhythm
- Max content width 1280px
- Persistent left sidebar for navigation; a detail panel slides in from the right
- Tables: zebra-free, subtle row separators, sticky header

---

## 3. Screens

### 3.1 Overview `/`

```
┌────────────────────────────────────────────────────────────────────┐
│  Revenue leakage overview                          [Last run: 2h]   │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐      │
│  │ Potential  │ │ Confirmed  │ │ Recovered  │ │ Open       │      │
│  │ leakage    │ │ leakage    │ │ revenue    │ │ cases      │      │
│  │ $284,620   │ │ $91,400    │ │ $63,800    │ │ 17         │      │
│  │ at risk    │ │ verified   │ │ this year  │ │ need review│      │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘      │
├────────────────────────────────────────────────────────────────────┤
│  Leakage over time                    │  Leakage by root cause      │
│  [line chart, 12 months]              │  [horizontal bars]          │
├───────────────────────────────────────┼─────────────────────────────┤
│  Highest-risk accounts                │  Leakage by product         │
│  [table: customer, exposure, cases]   │  [horizontal bars]          │
└────────────────────────────────────────────────────────────────────┘
```

**Every card states what the number means in small text under it.** "Potential
leakage" alone is ambiguous; "Potential leakage · at risk, not yet confirmed" is
not. This matters more than it sounds — it is the difference between a Finance user
trusting the dashboard and quietly ignoring it.

### 3.2 Case queue `/cases`

The main working screen. One row per **ongoing problem**, not one per month — a
five-month-old mismatch is one row showing "Apr – Aug".

Filters: status, leak type, confidence band, customer, date range. All persisted in
the URL so a filtered view can be shared.

```
Case   Customer        Issue                    At risk   Periods  Conf.  Status
───────────────────────────────────────────────────────────────────────────────
RL-417 Acme Corp       Amendment not applied   $18,000   Apr-Aug   94%    Awaiting
RL-418 Globex Ltd      Expired discount         $6,400   Jun-Aug   88%    Awaiting
RL-419 Initech         Usage above entitlement  $2,100   Jul-Aug   61%    Needs review
```

### 3.3 Case detail `/cases/[id]` — the most important screen

```
┌────────────────────────────────────────────────────────────────────┐
│  Revenue leakage investigation · RL-2026-00417                      │
│  Acme Corporation                          [94% confidence]         │
│  $18,000 at risk · April to August · Awaiting Finance review        │
├────────────────────────────────────────────────────────────────────┤
│  HOW THE SYSTEMS COMPARE                                            │
│   Contract 100 seats ──► CRM 100 ──► Impl. 100 ──► Usage 97         │
│                                                        ──► Billing 70│
│                                          MISMATCH: 30 seats          │
│                                          IMPACT: $3,600 / month      │
├────────────────────────────────────────────────────────────────────┤
│  WHY THIS WAS FLAGGED   │  EVIDENCE                                 │
│  [narrative + cause]    │  1. Contract §4.2 .......... [excerpt]    │
│                         │  2. Amendment AM-1042 ...... [excerpt]    │
│  WHAT CHANGED           │  3. CRM opportunity OP-8291               │
│  [timeline by system]   │  4. Invoice INV-18492                     │
│                         │                                           │
│  AGENT TRACE            │  ─────────────────────────────────────    │
│  [collapsed steps]      │  RECOMMENDED ACTION                       │
│                         │  Review billing quantity, issue           │
│                         │  adjustment.  [Approve]  [Reject]         │
└────────────────────────────────────────────────────────────────────┘
```

Requirements:
- The contract-to-mismatch chain is visible **as a chain**, not a table. This is
  the single most persuasive thing in the product.
- Every evidence item shows its source, record ID, date, and a quoted excerpt.
- Citations in the narrative are clickable and scroll to the evidence item.
- The agent trace is collapsed by default, expandable — proof of work without
  dominating the screen.
- **Approve requires a confirmation step.** Show what will happen before it happens.
- A `viewer` sees disabled action buttons with an explanation.

### 3.4 Other screens

| Route | Purpose |
|---|---|
| `/customers/[id]` | Revenue health, integrity score breakdown, case history |
| `/timeline` | "What changed" — field-level diffs grouped by system |
| `/ledger` | Recovered vs written-off vs still open |
| `/simulator` | "If we had caught this in month 1, we would have saved $X" |
| `/analytics` | Filterable breakdowns by month, customer, product, root cause |

---

## 4. Wording

Use these exact labels. Consistency here is what makes the demo video land.

| Say | Not |
|---|---|
| "Potential leakage" | "Lost revenue" |
| "Confirmed leakage" | "Definitely lost" |
| "Awaiting Finance review" | "Pending AI approval" |
| "Legitimate exception" | "False positive" |
| "Needs more information" | "AI is unsure" |
| "Detected by: usage/billing ratio" | "AI detected this" |
| "Recommended action" | "The AI suggests" |
| "Based on contract §4.2" | "Analysis shows" |

**Never say "the AI thinks".** Say what the system found and what evidence supports
it. The confidence number carries the uncertainty — the prose should not apologise
or boast.

---

## 5. States

Every screen needs all three designed, not just the happy path:

- **Empty** — explain what would appear and why it is empty. Never a blank panel.
- **Loading** — skeleton matching the final layout, so nothing jumps.
- **Error** — plain language, what failed, and a retry button.

Also: partial data. If half the evidence is unavailable, say so on the screen rather
than showing an incomplete case as though it were complete.

---

## 6. Badges

| Status | Treatment |
|---|---|
| Awaiting review | Warning |
| Confirmed for review | Danger |
| Valid exception | Success |
| Needs more information | Info |
| Resolved | Neutral |

Confidence renders as a number plus a bar: `94%` with a filled bar. Bands: high
(>90), medium (75–90), low (<75). Low confidence must look visibly different — it
means "do not trust this yet".

---

## 7. Accessibility

- All text meets contrast requirements
- Status is never conveyed by colour alone — always a label or icon too
- Every interactive element is keyboard reachable
- Tables have proper headers; charts have text alternatives
- No motion that could cause discomfort; honour reduced-motion preferences

---

## 8. Definition of done for any UI ticket

- [ ] Matches the visual language in section 2
- [ ] Uses the wording from section 4
- [ ] Empty, loading and error states all designed
- [ ] Keyboard accessible and contrast-checked
- [ ] Numbers come from the API — nothing hardcoded
- [ ] Works at 1280px and above without horizontal scrolling
- [ ] A viewer seeing it for the first time can tell what it does
