"""One detection run, and the counters that make it reproducible.

See TICKET-006 and ``docs/data-model.md``.

Plain-English: every pass of the detectors is a run. Recording the as-of date,
the engine version and a hash of the configuration means a number can be
explained six months later -- same inputs plus same config plus same version
gives the same answer.

A run is never edited once finished. Re-running creates a new run, which is why
``reconciliation_result`` carries ``run_id`` in its natural key (TICKET-006,
``derived/reconciliation_result.py``): two runs' results coexist side by side.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType

RUN_STATUS = Enum(
    "pending",
    "running",
    "succeeded",
    "failed",
    "cancelled",
    name="run_status",
    native_enum=False,
    length=32,
)


class ReconciliationRun(Base, TimestampMixin):
    """One execution of the detection pipeline."""

    __tablename__ = "reconciliation_run"

    # The date the run reasoned "as of". Money and period logic must never call
    # datetime.now() (AGENTS.md 1.5), so the as-of date is data, not a clock read.
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(RUN_STATUS, nullable=False, default="pending")

    # What the run covered: all customers, one customer, one scenario.
    scope: Mapped[str | None] = mapped_column(String(255))
    scenario_id: Mapped[str | None] = mapped_column(String(100))
    # Which scenario template and seed produced the data, when it was generated.
    dataset_version: Mapped[str | None] = mapped_column(String(100))
    seed: Mapped[int | None] = mapped_column(Integer)

    # Reproducibility: the engine that ran and the config it ran with.
    engine_version: Mapped[str | None] = mapped_column(String(64))
    # Hash of the normalised config, so identical configs hash identically.
    config_hash: Mapped[str | None] = mapped_column(String(128))
    git_sha: Mapped[str | None] = mapped_column(String(64))

    # Counters, so "how big was that run?" does not need a COUNT over results.
    customers_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    checks_executed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    results_written: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cases_opened: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cases_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # The headline number, in the reporting currency.
    total_delta_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())

    # Anything the run wants to record about itself: per-detector timings, warnings.
    details: Mapped[dict[str, object] | None] = mapped_column(JSON)
    error_detail: Mapped[str | None] = mapped_column(Text)


Index("ix_reconciliation_run_as_of_date", ReconciliationRun.as_of_date)
Index("ix_reconciliation_run_status", ReconciliationRun.status)
Index("ix_reconciliation_run_scenario_id", ReconciliationRun.scenario_id)

__all__ = ["ReconciliationRun"]
