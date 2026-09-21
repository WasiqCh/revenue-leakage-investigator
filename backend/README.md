# Backend

FastAPI application: ingestion, detection, investigation, API.

## Status

Not yet implemented. The design is in [`../docs/TRD.md`](../docs/TRD.md) and the
work is broken into tickets in [`../docs/tickets/`](../docs/tickets/). Start with
TICKET-001.

## What this means

This is the part that does the actual work. The website is only a window onto it.
Everything — reading contracts, comparing systems, running investigations,
computing money — happens here.

## Rules that apply to every file in here

Read [`../AGENTS.md`](../AGENTS.md) first. The three that matter most:

1. **The AI never computes money.** All arithmetic lives in `app/money/` and
   `app/billing/`. The LLM emits text and one enum, nothing numeric.
2. **The AI cannot write.** The agent runs as a read-only database role.
3. **Everything is verified.** `app/ai/verifier.py` re-checks every number in a
   report against the database before it reaches a human.

## Layout (once built)

```
app/
├── config.py       settings
├── db/             engine, session, custom types, guards
├── models/         source/ derived/ case/ ops/
├── money/          DecimalMoney, intervals, FX
├── billing/        periods, proration, expected revenue
├── detect/         reconciliation framework + checks + entity resolution
├── changefeed/     field-level diffs
├── cases/          fingerprinting, state machine, leakage, confidence
├── ai/             provider, tools, agent loop, verifier, report
├── rag/            chunking, embeddings, retrieval, clause extraction
├── jobs/           Postgres-backed queue and worker
├── eval/           golden-dataset evaluation
└── api/            FastAPI routers
```

## Running

Always through Docker, from the repo root:

```bash
make up          # start
make seed        # generate the dataset
make reconcile   # run detection
make investigate # run agent investigations
make test        # pytest, never touches the network
make eval        # evaluation scorecard
```

Direct commands inside the container:

```bash
docker compose exec backend python -m app.cli seed --seed 42 --customers 80
docker compose exec backend alembic upgrade head
docker compose exec backend pytest -q
```
