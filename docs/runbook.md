# Runbook

How to start, stop, reset and repair the AI Revenue Leakage Investigator.

Everything here assumes **Docker is installed and running**. There is no
non-Docker path — see
[ADR-002](adr/ADR-002-postgres-pgvector-docker-only.md).

---

## What this means

Four containers make up the whole system. Three are long-running services and one
is the database they all share.

| Container | Name | What it does | Port |
|---|---|---|---|
| Database | `rl_db` | PostgreSQL 16 with pgvector. Holds records, cases, jobs, vectors and the audit trail. | 5432 |
| API | `rl_backend` | FastAPI. Serves the website and the OpenAPI schema. | 8000 |
| Worker | `rl_worker` | Takes jobs off the Postgres queue and runs reconciliations and investigations. | — |
| Website | `rl_frontend` | Next.js. The screens Finance uses. | 3000 |

The worker is the part people forget. **If the worker is not running,
investigations never start** — cases will sit at `Detected` forever and the
queue will look broken when it is not.

Useful URLs once running:

- Website: http://localhost:3000
- API docs (OpenAPI): http://localhost:8000/docs

---

## Starting and stopping

```bash
make up      # start everything (builds images the first time)
make down    # stop everything
make logs    # tail logs from all services
```

`make up` builds and starts all four containers. The first run takes longer
because images are built; subsequent runs are quick.

**Stopping does not delete data.** The database lives in a named Docker volume
(`postgres_data`), so `make down` followed by `make up` brings back exactly the
same dataset.

To follow one service only:

```bash
docker compose logs -f worker     # watch investigations run
docker compose logs -f backend    # watch API requests
docker compose logs -f db         # watch the database
```

To stop and also remove the containers but keep the data volume:

```bash
docker compose down
```

To stop and **destroy the data** as well — this is irreversible:

```bash
docker compose down -v
```

---

## Getting to a working demo state

The first time, in this order:

```bash
cp .env.example .env      # then fill in LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
make up
make migrate              # apply database migrations
make seed                 # generate the synthetic company dataset
make reconcile            # run detection
make investigate          # run agent investigations
```

Then open http://localhost:3000.

Or the whole sequence in one command:

```bash
make demo                 # seed + reconcile + investigate
```

**The order matters.** `make seed` must run before `make reconcile`, because
detection has nothing to detect until the dataset exists. `make reconcile` must
run before `make investigate`, because there are no cases to investigate until
detection has created them.

`make seed` runs with `--reset`, so it clears the generated data first. It is
idempotent: running it twice with the same seed produces byte-identical output.

---

## Resetting the dataset

### Reset the data, keep the containers

This is the normal reset. Use it between demo takes.

```bash
make seed        # regenerates the dataset and clears prior cases
make reconcile
make investigate
```

### Reset with a different random seed

To get a different synthetic company — different customers, different injected
patterns, same structure:

```bash
docker compose exec backend python -m app.cli seed --reset --seed 12345
```

### Reset a different size of company

The default dataset is sized for a demo. To generate more customers:

```bash
docker compose exec backend python -m app.cli seed --reset --customers 200
```

### Full reset — schema and data

If the schema itself is wrong or a migration is half-applied, rebuild from
scratch. **This destroys everything in the database.**

```bash
make down
docker compose down -v        # removes the postgres_data volume
make up
make migrate
make seed
```

If you only want to re-apply migrations without dropping the volume:

```bash
make migrate
```

### Reset the CUAD cache

The contract cache lives outside the repository. To force a fresh download:

```bash
rm -rf data/cuad
make fetch-cuad
```

Note that `make fetch-cuad` needs network access and about 106 MB. It is
**optional** — the test suite runs entirely offline against a small committed
fixture when `CUAD_OFFLINE=1`.

---

## The top five failure modes

### 1. Database not healthy, or the vector extension is missing

**Symptom**

- `make up` returns but the API and worker crash-loop in `make logs`.
- Errors containing `connection refused`, `could not connect to server`, or
  `role "rl_readonly" does not exist`.
- `type "vector" does not exist` when a migration runs.
- The health check never goes green and dependent containers never start.

**Cause**

The database container is not actually accepting connections yet, or the
`postgres_data` volume was created before `scripts/init_db.sql` existed. That
script runs **only on first creation of the volume**, so a volume created
earlier will be missing the `vector` extension, the `pg_trgm` extension and the
`rl_readonly` role.

**Fix**

Check the database first:

```bash
docker compose ps                       # is rl_db "healthy"?
docker compose logs db | tail -50
make db-shell                           # opens psql; if this works, the DB is fine
```

If psql connects, confirm the extensions and the role exist:

```sql
\dx                                     -- should list vector, pg_trgm, pgcrypto
\du                                     -- should list rl_readonly and rl_app
```

If they are missing, the volume predates `init_db.sql`. Rebuild it:

```bash
make down
docker compose down -v
make up
make migrate
make seed
```

If the database is simply not up yet, wait — the health check retries every 5
seconds up to 20 times, and the API and worker wait for it. If it still fails
after that, check Docker has enough memory allocated.

---

### 2. Agent investigations hang, or exhaust their budget

**Symptom**

- Cases stay at `Investigating` and never reach `Awaiting Finance Review`.
- Worker logs show `terminal_reason=budget_exhausted`.
- The same case is investigated repeatedly with no conclusion.
- The investigation trace stops mid-phase.

**Cause**

The agent loop is deliberately bounded. It has a tool-call budget and a token
budget, and it stops when either is exhausted rather than running forever. A
budget-exhausted run means the agent could not reach a conclusion within its
limits — usually because the evidence it needed does not exist in the dataset,
or because the question is genuinely ambiguous.

This is **working as designed**, not a crash. A loop that never concludes is
supposed to terminate and say so.

**Fix**

Look at the case's investigation trace first. If the trace shows the agent
repeatedly calling the same tool, the prompt or the tool result is the problem.
If the trace shows the agent looking for evidence that is not there, the case
should end as `NEEDS_REVIEW` and that is the correct outcome — do not raise the
budget to force a conclusion.

If you need to confirm the budgets in force:

```bash
docker compose exec backend python -c "from app.config import settings; print(settings.agent_tool_budget, settings.agent_token_budget)"
```

To re-run a single investigation after fixing something:

```bash
docker compose exec backend python -m app.cli investigate --case <case-id>
```

Then check the job and trace tables for the real story:

```sql
SELECT id, status, attempts, last_error FROM job WHERE status <> 'done' ORDER BY id DESC LIMIT 20;
SELECT case_id, step_index, phase, tool_name FROM agent_trace_step ORDER BY case_id, step_index LIMIT 50;
```

**Do not raise the budget to make a stuck case finish.** A case that cannot be
concluded should be escalated to a human, not forced.

---

### 3. Confidence scores all land in one band

**Symptom**

- Every case shows a confidence of, say, `94%`, or every case shows `60%`.
- The score does not change between very different cases.
- Everything sits just below the review threshold, or everything sits just above.

**Cause**

Three possibilities, in order of likelihood:

1. **A gate is capping everything.** The confidence engine has five hard gates
   that can only ever *lower* a score. If the verifier is failing broadly, every
   score is capped at 60. If a required evidence type is missing broadly, every
   score is capped at 74.
2. **The factors are not being populated.** If the input factors are all
   identical (for example, every case is missing the same evidence type), the
   output will be identical too.
3. **The score is being read from the wrong place.** The confidence score must
   come from `cases/confidence.compute_confidence()`. If a value from the model
   or from a default has leaked into the field, every case will show the same
   number.

**Fix**

First check whether a gate is firing. Query the verifier report alongside the
score:

```sql
SELECT c.id, c.confidence, c.status, v.passed, v.reason
FROM case c LEFT JOIN verifier_report v ON v.case_id = c.id
ORDER BY c.confidence LIMIT 20;
```

If `verifier_report.passed` is false across the board, the problem is the
verifier, not the confidence engine — go to failure mode 5.

If the verifier is passing and the scores are still identical, check that the
eight input factors actually differ between cases:

```sql
SELECT case_id, factor_name, factor_value FROM confidence_factor ORDER BY case_id, factor_name LIMIT 40;
```

If every factor value is the same, the factor computation is broken, not the
scoring.

Remember that only one of the eight factors comes from the model
(`contract_clarity`). If that is the only one changing and everything else is
constant, the deterministic inputs are not being supplied.

---

### 4. Duplicate cases appearing

**Symptom**

- The same customer and the same problem appear as five separate rows, one per
  month, instead of one row with a five-period range.
- Re-running `make reconcile` increases the case count.
- The queue grows on every run without new data.

**Cause**

Case creation must always fingerprint before inserting. The fingerprint is a
deterministic hash over `(customer, subscription_line, leak_type, product)` and
**deliberately excludes the billing period** — that is what collapses a repeating
mismatch into one case. A duplicate means either the fingerprint is including the
period, or the upsert is inserting instead of updating.

**Fix**

Confirm the scale of the problem:

```sql
SELECT case_key, count(*) FROM case GROUP BY case_key HAVING count(*) > 1;
```

A non-empty result means duplicates exist. To confirm the idempotency guarantee
is broken, run detection twice and compare counts:

```bash
make reconcile
docker compose exec db psql -U rl_app -d revenue_leakage -c "SELECT count(*) FROM case;"
make reconcile
docker compose exec db psql -U rl_app -d revenue_leakage -c "SELECT count(*) FROM case;"
```

The two counts must be identical. If they are not, the fingerprint or the upsert
is the bug — this is a genuine defect, not an operational issue, so raise it
rather than working around it.

To clear the duplicates and start clean:

```bash
make seed        # resets generated data and cases
make reconcile
```

Note that two *different* leak types on the same subscription line **should**
produce two cases. That is correct behaviour, not a duplicate.

---

### 5. LLM provider errors or rate limits

**Symptom**

- Worker logs show `401`, `403`, `429`, or `timeout` from the provider.
- Cases fail with a provider error and retry, then dead-letter.
- Investigations are slow or stop entirely while detection still works.
- `make test` is fine but `make investigate` fails.

**Cause**

Either the credentials or endpoint in `.env` are wrong, or the provider is rate
limiting or unavailable. Note that `make test` **never touches the network** — it
runs with `LLM_MOCK=1` — so a passing test suite says nothing about whether your
real provider configuration works.

**Fix**

Check the configuration first:

```bash
docker compose exec backend python -c "from app.config import settings; print(settings.llm_base_url, settings.llm_model, bool(settings.llm_api_key))"
```

Then check the call ledger, which records every model call and its outcome:

```sql
SELECT id, case_id, status, http_status, error, created_at
FROM llm_call ORDER BY id DESC LIMIT 20;
```

For a `401` or `403`, the key or the base URL is wrong. Fix `.env` and restart
the containers that read it — **environment variables are read at container
start, so an `.env` change needs a restart:**

```bash
docker compose up -d --force-recreate backend worker
```

For a `429` or repeated timeouts, the job queue already retries with exponential
backoff. Wait for the retries rather than restarting, and check the queue state:

```sql
SELECT status, count(*) FROM job GROUP BY status;
```

If you need to work offline — for a demo rehearsal, or to test the pipeline
without spending tokens — set the mock provider:

```bash
LLM_MOCK=1
```

then recreate the worker. The mock provider is deterministic and returns
scripted responses, so investigations complete without any network call. This is
also how the test suite runs.

If jobs have dead-lettered after exhausting their attempts, re-queue them:

```bash
docker compose exec backend python -m app.cli investigate --all --requeue
```

---

## Inspecting a stuck job

A job that is claimed but never finishes holds its lock. Start here.

**What is the job doing?**

```sql
SELECT id, kind, status, attempts, max_attempts, locked_by, locked_at, last_error
FROM job
WHERE status IN ('claimed', 'running')
ORDER BY locked_at;
```

Key columns:

| Column | What to look for |
|---|---|
| `status` | `queued`, `claimed`, `running`, `done`, `dead_letter` |
| `attempts` vs `max_attempts` | If they are equal and the status is `dead_letter`, it has given up |
| `locked_by` | Which worker holds it |
| `locked_at` | How long it has been held. A long-held lock with no progress means a stuck worker |
| `last_error` | The actual failure reason. Read this before anything else |

**Is the worker alive?**

```bash
docker compose ps worker
docker compose logs --tail=100 worker
```

If the worker container has exited, `make up` brings it back. A graceful shutdown
releases the lock; a hard kill does not, which is why `locked_at` matters.

**What has the case actually done?**

```sql
SELECT case_id, step_index, phase, tool_name, created_at
FROM agent_trace_step
WHERE case_id = '<case-id>'
ORDER BY step_index;
```

If the trace stops abruptly mid-phase, the worker died during that step. If the
trace is complete but the case never advanced, the state transition failed.

**What is the case's current state?**

```sql
SELECT id, status, confidence, updated_at FROM case WHERE id = '<case-id>';
SELECT * FROM audit_event WHERE case_id = '<case-id>' ORDER BY id;
```

The audit trail records every state change, so if the case moved, there is an
event for it. If there is no event, the transition never happened.

**Recovering**

For a job whose lock is stale and whose worker is gone, release and re-queue:

```bash
docker compose restart worker
docker compose exec backend python -m app.cli investigate --case <case-id> --requeue
```

For a dead-lettered job, fix the underlying cause first — re-queueing without
fixing it will simply dead-letter again.

---

## Re-running evaluation

The evaluation harness scores detection precision and recall, exception
classification and confidence calibration against the golden dataset.

```bash
make eval
```

Or explicitly, across all suites:

```bash
docker compose exec backend python -m app.cli eval --suite all
```

Individual suites:

```bash
docker compose exec backend python -m app.cli eval --suite detection
docker compose exec backend python -m app.cli eval --suite exceptions
docker compose exec backend python -m app.cli eval --suite calibration
docker compose exec backend python -m app.cli eval --suite clause_extraction
```

**Evaluation must run against a seeded dataset.** If the scores look like zero or
`n/a`, the golden labels are probably missing:

```sql
SELECT count(*) FROM golden_label;
```

If that is zero, run `make seed` first.

Results are written to `eval_run` and `eval_result` and are reproducible from the
git SHA plus the dataset version:

```sql
SELECT id, git_sha, dataset_version, started_at FROM eval_run ORDER BY id DESC LIMIT 10;
SELECT suite, metric, value FROM eval_result WHERE eval_run_id = <id>;
```

Two runs with the same git SHA and the same dataset version must produce the same
numbers. If they do not, something in the pipeline is non-deterministic, which is
a defect worth investigating rather than a flaky result to ignore.

The optional managed-RAG baseline suite (TICKET-048) skips cleanly when no
credentials are configured, and still passes. That is expected.

---

## If the verifier rejects everything

This is the most serious failure mode, because the verifier is the component
that stops the AI inventing numbers. If it is rejecting everything, either the
verifier is broken or the reports genuinely are.

**Symptoms**

- Every case is capped at a confidence of 60.
- Every case ends at `NEEDS_REVIEW`.
- Verifier reports cite fabricated amounts or non-existent evidence rows.

**Diagnose**

Look at what the verifier actually objected to:

```sql
SELECT case_id, passed, reason, detail FROM verifier_report WHERE passed = false ORDER BY case_id LIMIT 20;
```

The reason tells you which of these you are facing:

| Verifier reason | What it means | What to do |
|---|---|---|
| A numeric claim has no matching tool result | The report contains a number that no recorded tool call produced | This is the verifier working correctly. The report generation is emitting a number it should not — fix report generation, do not weaken the verifier. |
| Cited evidence row does not exist | The report cites an evidence id that is not in the database | Evidence rows are being deleted or not committed before the report is written. Check the ordering in the investigation pipeline. |
| Grounding check failed | Extracted text is not present in the source record | Clause extraction is paraphrasing instead of quoting. Fix extraction so it returns spans that exist verbatim. |
| Every claim fails | Usually a systemic mismatch between how claims are recorded and how they are looked up | Suspect a schema or key mismatch introduced by a recent change. |

**First, establish whether it is systemic.** Pick one case that *should* pass —
a clean, rule-detected case with complete evidence — and inspect it directly:

```sql
SELECT * FROM evidence WHERE case_id = '<case-id>';
SELECT * FROM investigation_report WHERE case_id = '<case-id>';
```

If the evidence exists and the report's claims match it, but the verifier still
rejects, the verifier is broken.

**Second, check the recent history.** If the verifier started rejecting
everything at a specific point, find the change:

```sql
SELECT count(*) FILTER (WHERE passed) AS passed, count(*) FILTER (WHERE NOT passed) AS failed
FROM verifier_report;
```

If `passed` is zero across the whole table, the verifier has probably never
worked in this environment, which points at a configuration or schema problem
rather than a data problem.

**Third, decide honestly which side is wrong.**

- If the reports contain numbers that no tool produced, **the verifier is right
  and the report generator is wrong.** Fix the report generator. This is exactly
  the failure the verifier exists to catch.
- If the reports are fully grounded and the verifier still fails them, **the
  verifier is wrong.** Fix the verifier.

**Never do this:** weaken the verifier's checks, or raise the confidence cap, to
make cases pass. The verifier rejecting a fabricated number is the single most
valuable behaviour in the system. Turning it off to make the queue look healthier
removes the only thing standing between a hallucinated dollar figure and a
Finance report.

If you cannot tell which side is wrong, stop and ask. This is a case where
guessing is expensive.

---

## Quick reference

| Task | Command |
|---|---|
| Start everything | `make up` |
| Stop everything | `make down` |
| Follow all logs | `make logs` |
| Follow one service | `docker compose logs -f worker` |
| Open a SQL prompt | `make db-shell` |
| Apply migrations | `make migrate` |
| Regenerate the dataset | `make seed` |
| Run detection | `make reconcile` |
| Run investigations | `make investigate` |
| Seed + reconcile + investigate | `make demo` |
| Run the test suite (offline) | `make test` |
| Run the evaluation scorecard | `make eval` |
| Download the CUAD dataset (optional) | `make fetch-cuad` |
| Lint and type-check | `make lint` |
| Recreate a container after an `.env` change | `docker compose up -d --force-recreate backend worker` |
| Destroy all data and start clean | `make down && docker compose down -v && make up && make migrate && make seed` |

---

## Where to go next

- What the product is: [../README.md](../README.md)
- What every term means: [glossary.md](glossary.md)
- How to record the demo: [demo-script.md](demo-script.md)
- The state machine a case moves through: [case-lifecycle.md](case-lifecycle.md)
- How confidence is computed: [confidence.md](confidence.md)
