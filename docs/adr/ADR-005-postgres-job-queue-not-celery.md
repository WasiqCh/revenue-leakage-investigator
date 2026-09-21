# ADR-005: Background jobs use a Postgres table, not Celery or a message broker

**Status:** Accepted — 2026-09-21

## What this means

Reconciliation and investigation take too long to run while a user waits, so they run in the background and we need somewhere to hold "work waiting to be done". The usual answer is a separate **message broker** — software whose only job is to hold a queue of tasks — plus a **task framework** like Celery to move work through it. We are not doing that. The queue is an ordinary table in the database we already run, called `job`. A **worker** claims work with one database statement that marks the next unclaimed row as taken and returns it; the `FOR UPDATE SKIP LOCKED` clause tells Postgres to give each worker a different row and let the others skip over the locked ones, so two workers never take the same job. Retries, timeouts, failures and progress are just columns on that table. Running the system means running Postgres — no Redis, RabbitMQ, Kafka or n8n.

## Context

Infrastructure is paid for forever: it must be installed, configured, monitored, secured, backed up, upgraded and explained to whoever inherits the project. A broker is a second stateful system with its own failure modes and its own way of losing messages. Our workload does not justify that: a nightly reconciliation over 50–100 customers with 12 months of history, and a few hundred investigations per run. That is minutes of work, not millions of messages per second. The brief for this work also says explicitly not to add infrastructure in order to look sophisticated, and adding a broker to a system whose whole argument is that it is small and auditable would undercut the argument. There is a correctness benefit too: when the queue shares the database with case data, claiming a job and updating the case happen in one transaction, whereas an external broker can retry a crashed task into a duplicate — exactly the duplicate-case problem we have committed to eliminating.

## Decision

**Background jobs use a Postgres `job` table, claimed with `SELECT ... FOR UPDATE SKIP LOCKED`. No Celery, no Redis, no RabbitMQ, no Kafka, no n8n.**

- `job` carries `id`, `kind`, `payload`, `status`, `attempts`, `max_attempts`, `run_after`, `locked_at`, `locked_by`, `last_error`, `created_at` and `finished_at`.
- Claiming is one statement: select the oldest due row with `FOR UPDATE SKIP LOCKED`, then set `status='RUNNING'`, `locked_by` and `locked_at`.
- Failures retry with exponential backoff via `run_after`; exhausted jobs become `status='DEAD'` and raise a visible alert rather than disappearing silently.
- Workers are stateless and several may run at once; a reaper releases rows whose `locked_at` is stale, recovering crashed workers.
- Jobs are idempotent — a retry re-checks the case fingerprint before writing — which is what makes at-least-once delivery safe.

## Alternatives considered

- **Celery with Redis or RabbitMQ.** Rejected. The default answer and a good one at scale, but here it adds a second stateful service and a second dependency ecosystem for a workload one table handles, and it separates the queue from the data, reintroducing the transactional gap.
- **Redis alone as a queue (RQ, lists, streams).** Rejected. Redis persistence makes the queue the least durable part of an otherwise durable system, which is backwards — losing a job should not be easier than losing a case.
- **RabbitMQ or Kafka.** Rejected. Both are over-scoped here. Kafka in particular is a log, not a task queue, so using it as one means building the retry and dead-letter semantics we would have to build anyway.
- **n8n or a visual workflow tool.** Rejected. It moves orchestration out of the repository into a UI where it cannot be reviewed, tested or versioned, and it adds a service and a licence conversation.
- **APScheduler or in-process threads.** Rejected. Work is lost on restart and cannot be spread across the API and worker containers.
- **A managed cloud queue (SQS, Cloud Tasks).** Rejected for the default path: credentials and cost in `make test`, and a network dependency in the demo.

## Consequences

**Easier.** One datastore and one thing to run. Enqueue and state change share a transaction, so no job can succeed without its effect being visible. The queue is inspectable with the same SQL as everything else, so a stuck job is a `SELECT` away and can be shown in the UI for free. Operational behaviour is fully reproducible in tests because it is plain Postgres.

**Harder.** Polling replaces push, so there is a small latency between enqueue and pickup and idle workers still query the database. At much higher throughput the `job` table becomes a hot spot needing partitioning and careful index work. We also implement retry, backoff, timeouts and a reaper ourselves, which a framework would have provided.

**Negative.** We are building a queue, a category of software that is easy to get subtly wrong. Our first version will be correct but plain: no priority classes, no per-tenant fairness, no scheduling beyond `run_after`. At thousands of tenants this decision will be revisited, and the migration will be a real project rather than a config change.

## How to reverse it

Adopting a broker means writing a producer and consumer against it, keeping or migrating the `job` history, and re-implementing the transaction boundary that currently guarantees a job's effect is committed with its claim. The job handlers themselves survive unchanged.
