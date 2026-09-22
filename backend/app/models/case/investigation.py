"""One investigation: the run, the report it produced, and its trace.

See TICKET-006, ``docs/data-model.md`` and ``docs/agent-loop.md``.

Plain-English: when the agent looks into a case it spends bounded resources -- so
many tool calls, so many tokens. ``investigation_run`` records the budget and what
was actually spent, plus why it stopped. ``agent_trace_step`` is the step-by-step
log, and ``investigation_report`` is the write-once answer.

Two rules from ``docs/data-model.md`` are encoded here rather than left to
convention:

- ``agent_trace_step`` is append-only, so "what did the agent actually do?" is
  answerable after the fact. (The trigger that blocks UPDATE and DELETE arrives
  in TICKET-007; the schema already marks it as having no mutable fields.)
- ``investigation_report`` is versioned and never overwritten, so a second
  investigation of the same case adds report version 2 rather than editing
  version 1.
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType

TERMINAL_REASON = Enum(
    "completed",
    "budget_exhausted",
    "max_steps_reached",
    "low_confidence",
    "verifier_rejected",
    "error",
    name="terminal_reason",
    native_enum=False,
    length=32,
)

TRACE_PHASE = Enum(
    "plan",
    "retrieve",
    "inspect",
    "compute",
    "verify",
    "report",
    name="trace_phase",
    native_enum=False,
    length=32,
)


class InvestigationRun(Base, TimestampMixin):
    """One execution of the agent against one case, with its budgets."""

    __tablename__ = "investigation_run"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    # Which attempt this is for the case: 1, 2, 3... A re-investigation never
    # edits the previous run's row.
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # e.g. "v1.0.0" -- lets us tell which code produced which findings.
    agent_version: Mapped[str | None] = mapped_column(String(64))

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    # Budget vs spend. The loop is bounded: it must stop when either runs out.
    max_steps: Mapped[int | None] = mapped_column(Integer)
    steps_used: Mapped[int | None] = mapped_column(Integer)
    max_tool_calls: Mapped[int | None] = mapped_column(Integer)
    tool_calls_used: Mapped[int | None] = mapped_column(Integer)
    token_budget: Mapped[int | None] = mapped_column(Integer)
    tokens_used: Mapped[int | None] = mapped_column(Integer)

    # Why the loop stopped -- see TERMINAL_REASON.
    terminal_reason: Mapped[str | None] = mapped_column(TERMINAL_REASON)
    error_detail: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("case_id", "attempt", name="uq_investigation_run_case_attempt"),
    )


class InvestigationReport(Base, TimestampMixin):
    """The versioned write-once answer for a case."""

    __tablename__ = "investigation_report"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("investigation_run.id", ondelete="SET NULL")
    )
    # Versioned, never overwritten: a second pass writes version 2.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    hypothesis: Mapped[str | None] = mapped_column(Text)
    narrative: Mapped[str | None] = mapped_column(Text)
    # e.g. price_propagation_gap | contract_not_amended | usage_ingestion_gap
    root_cause_category: Mapped[str | None] = mapped_column(String(100))

    proposed_correction: Mapped[str | None] = mapped_column(Text)
    proposed_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())

    # The single permitted qualitative factor: a human-readable multiplier
    # rationale, never a number the model invented. Money stays Decimal and is
    # computed by code, not by the model (AGENTS.md 1.1).
    qualitative_factor: Mapped[str | None] = mapped_column(String(255))
    qualitative_note: Mapped[str | None] = mapped_column(Text)

    # Which clauses the report leaned on, as [{"source_clause_id": ..., "score": ...}].
    citations: Mapped[list[dict[str, object]] | None] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint("case_id", "version", name="uq_investigation_report_case_version"),
    )


class AgentTraceStep(Base, TimestampMixin):
    """One step of the agent loop. Append-only (TICKET-007 adds the trigger)."""

    __tablename__ = "agent_trace_step"

    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigation_run.id", ondelete="CASCADE"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str | None] = mapped_column(TRACE_PHASE)

    tool_name: Mapped[str | None] = mapped_column(String(100))
    # The exact arguments, so a step can be replayed.
    tool_args: Mapped[dict[str, object] | None] = mapped_column(JSON)
    result_summary: Mapped[str | None] = mapped_column(Text)

    tokens_used: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    # Did the Verifier accept this step? Null means "not verified yet".
    verified: Mapped[bool | None] = mapped_column(Boolean)

    __table_args__ = (
        UniqueConstraint("run_id", "step_index", name="uq_agent_trace_step_run_step"),
    )


class QaMessage(Base, TimestampMixin):
    """One turn of the case-scoped "ask the investigator" chat."""

    __tablename__ = "qa_message"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    # question | answer
    role: Mapped[str] = mapped_column(
        Enum("question", "answer", name="qa_role", native_enum=False, length=16),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Which source rows back the answer, as [{"source_table": ..., "source_id": ...}].
    citations: Mapped[list[dict[str, object]] | None] = mapped_column(JSON)
    # True when the endpoint declined to answer -- out of scope, or no evidence.
    refused: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    refusal_reason: Mapped[str | None] = mapped_column(String(255))
    # Which model answered, and what it cost, when one did.
    model: Mapped[str | None] = mapped_column(String(100))
    tokens_used: Mapped[int | None] = mapped_column(Integer)


Index("ix_investigation_run_case_id", InvestigationRun.case_id)
Index("ix_investigation_run_terminal_reason", InvestigationRun.terminal_reason)
Index("ix_investigation_report_case_id", InvestigationReport.case_id)
Index("ix_investigation_report_root_cause", InvestigationReport.root_cause_category)
Index("ix_agent_trace_step_run_id", AgentTraceStep.run_id)
Index("ix_agent_trace_step_phase", AgentTraceStep.run_id, AgentTraceStep.phase)
Index("ix_qa_message_case_id", QaMessage.case_id)

__all__ = ["AgentTraceStep", "InvestigationReport", "InvestigationRun", "QaMessage"]
