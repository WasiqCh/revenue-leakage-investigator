# TICKET-032 - Postgres job queue and worker loop

- **Status:** TODO
- **Phase:** 5 - AI layer
- **Effort:** 1.5 day
- **Depends on:** TICKET-006, TICKET-029

## Goal

A durable job table and worker process for background reconciliation and investigation.

## What this means

Long investigations run in the background so the website stays fast. Uses a table in Postgres rather than adding Redis or Celery - one less piece of infrastructure to run.

## Context

FOR UPDATE SKIP LOCKED claiming, exponential backoff, max attempts, dead-lettering.

## Deliverables

- `backend/app/jobs/queue.py`
- `backend/app/jobs/worker.py`
- `backend/tests/integration/test_job_queue.py`

## Acceptance criteria

- [ ] two workers concurrently claim distinct jobs with no double-processing
- [ ] a failing job retries then dead-letters after max_attempts
- [ ] a graceful shutdown releases the lock
- [ ] a worker restart resumes queued jobs

## Definition of done

- [ ] every deliverable file exists
- [ ] every acceptance criterion above is checked off
- [ ] `make test` passes
- [ ] no rule in `AGENTS.md` was violated
- [ ] status updated to DONE and committed with the co-author trailer
