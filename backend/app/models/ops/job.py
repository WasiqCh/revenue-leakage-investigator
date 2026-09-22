"""The work queue and the ledger of every model call.

See TICKET-006, ``docs/data-model.md`` and ``docs/adr/ADR-005-postgres-job-queue-not-celery.md``.

Plain-English: there is no Redis and no Celery here. The queue is an ordinary
Postgres table, and a worker claims a row with ``SELECT ... FOR UPDATE SKIP
LOCKED`` -- which means two workers can run at once without stepping on each
other, and a crashed worker's row becomes visible again.

``llm_call`` is the cost ledger. Every model call is recorded with its purpose,
prompt hash, tokens and latency, so "what did this investigation cost?" is a
query rather than an estimate.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.enums import JobStatus
from app.db.types import CurrencyCode, MoneyType

JOB_STATUS = Enum(
    JobStatus,
    name="job_status",
    native_enum=False,
    length=32,
    values_callable=lambda enum: [member.value for member in enum],
)

LLM_CALL_STATUS = Enum(
    "succeeded",
    "failed",
    "timeout",
    "mock",
    name="llm_call_status",
    native_enum=False,
    length=32,
)


class Job(Base, TimestampMixin):
    """One unit of background work. The whole queue is this table."""

    __tablename__ = "job"

    # e.g. detect | investigate | ingest | embed | evaluate
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(JOB_STATUS, nullable=False, default="pending")

    # The arguments, as JSON. Kept small and serialisable on purpose.
    payload: Mapped[dict[str, object] | None] = mapped_column(JSON)
    result: Mapped[dict[str, object] | None] = mapped_column(JSON)
    error_detail: Mapped[str | None] = mapped_column(Text)

    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    # When a failed job becomes claimable again. Null means "claimable now".
    run_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Who holds the row. Set on claim, cleared when the job finishes.
    locked_by: Mapped[str | None] = mapped_column(String(255))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Lower number runs first; ties break on created_at.
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    # Deduplication: a job already queued with this key is not queued again.
    dedupe_key: Mapped[str | None] = mapped_column(String(255))
    # Optional link back to the case or run the job belongs to.
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("case.id", ondelete="CASCADE"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    # Set once the job has been fully processed, so history is kept not deleted.
    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class LlmCall(Base, TimestampMixin):
    """One model call: what it was for, what it cost, how long it took."""

    __tablename__ = "llm_call"

    # Why the call was made: clause_extraction | report | qa | triage
    purpose: Mapped[str] = mapped_column(String(100), nullable=False)
    # e.g. "openrouter/anthropic/claude-3.5-sonnet"
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(LLM_CALL_STATUS, nullable=False, default="mock")

    # Hash of the prompt, not the prompt text: enough to detect a repeat call
    # without storing every payload.
    prompt_hash: Mapped[str | None] = mapped_column(String(128))
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    # Cost is money, so it is exact numeric -- never a float (AGENTS.md 1.4).
    cost_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    cost_currency: Mapped[str | None] = mapped_column(CurrencyCode())

    # Traceability back to what triggered the call.
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("case.id", ondelete="CASCADE"))
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("investigation_run.id", ondelete="SET NULL")
    )
    trace_step_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("agent_trace_step.id", ondelete="SET NULL")
    )
    # True when the mock provider answered instead of a real model -- tests must
    # never touch the network (AGENTS.md 1.6).
    mocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error_detail: Mapped[str | None] = mapped_column(Text)


Index("ix_job_status", Job.status)
Index("ix_job_type", Job.job_type)
Index("ix_job_run_after", Job.run_after)
Index("ix_job_dedupe_key", Job.dedupe_key, unique=True)
Index("ix_job_case_id", Job.case_id)
Index("ix_llm_call_purpose", LlmCall.purpose)
Index("ix_llm_call_model", LlmCall.model)
Index("ix_llm_call_case_id", LlmCall.case_id)
Index("ix_llm_call_run_id", LlmCall.run_id)

__all__ = ["Job", "LlmCall"]
