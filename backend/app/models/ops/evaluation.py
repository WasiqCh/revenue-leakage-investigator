"""Evaluation runs and their scored items.

See TICKET-006 and ``docs/data-model.md``.

Plain-English: an eval run is one pass of the scoring suite over a dataset, and
each item inside it records what was expected, what the system produced, and
whether that counted as a pass. Stamping the run with the git SHA and dataset
version means a score quoted in a report can be traced back to the exact code
and data that produced it.

Scoring is stored as exact numeric, never a float -- the same rule that governs
money (AGENTS.md 1.4).
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
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

EVAL_SUITE = Enum(
    "retrieval",
    "extraction",
    "detection",
    "case_clustering",
    "confidence",
    "end_to_end",
    name="eval_suite",
    native_enum=False,
    length=32,
)


class EvalRun(Base, TimestampMixin):
    """One execution of an evaluation suite."""

    __tablename__ = "eval_run"

    suite: Mapped[str] = mapped_column(EVAL_SUITE, nullable=False)
    # Traceability: which code and which data produced this score.
    git_sha: Mapped[str | None] = mapped_column(String(64))
    dataset_version: Mapped[str | None] = mapped_column(String(100))
    scenario_id: Mapped[str | None] = mapped_column(String(100))
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reconciliation_run.id", ondelete="SET NULL")
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Aggregate scores, exact numeric with four decimal places.
    precision: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    recall: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    f1: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    # Suite-specific knobs -- e.g. the k used for recall@k.
    parameters: Mapped[dict[str, object] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)


class EvalResult(Base, TimestampMixin):
    """One scored item inside an eval run: expected, actual, pass flag, score."""

    __tablename__ = "eval_result"

    eval_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("eval_run.id", ondelete="CASCADE"), nullable=False
    )
    # What was scored: a clause, a case, a detector result.
    item_type: Mapped[str] = mapped_column(String(100), nullable=False)
    item_ref: Mapped[str | None] = mapped_column(String(255))
    golden_label_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("golden_label.id", ondelete="SET NULL")
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("case.id", ondelete="SET NULL"))

    expected: Mapped[dict[str, object] | None] = mapped_column(JSON)
    actual: Mapped[dict[str, object] | None] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(9, 4))
    # Why it failed, when it did -- e.g. missed_period | wrong_amount | wrong_type.
    failure_mode: Mapped[str | None] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(Text)


Index("ix_eval_run_suite", EvalRun.suite)
Index("ix_eval_run_git_sha", EvalRun.git_sha)
Index("ix_eval_result_eval_run_id", EvalResult.eval_run_id)
Index("ix_eval_result_item", EvalResult.item_type, EvalResult.item_ref)
Index("ix_eval_result_passed", EvalResult.passed)
Index("ix_eval_result_failure_mode", EvalResult.failure_mode)

__all__ = ["EvalResult", "EvalRun"]
