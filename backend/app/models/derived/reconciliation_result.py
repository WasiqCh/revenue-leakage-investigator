"""The output of one check, and the field-level diffs behind it.

See TICKET-006 and ``docs/data-model.md``.

Plain-English: ``reconciliation_result`` is the raw "expected vs actual" answer
for one customer, one line and one period. It is deliberately kept apart from
``case``: a case is five months of the same problem grouped into one, while this
row is one measurement. Keeping them separate is what lets detection be re-run
and produce an identical result.

``change_event`` answers a different question -- "what changed?" -- by storing a
field-level before/after rather than a money delta.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, Index, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType


class ReconciliationResult(Base, TimestampMixin):
    """One check against one line for one period: expected, actual, delta."""

    __tablename__ = "reconciliation_result"

    # Which detection run produced this row. Two runs must be able to coexist, so
    # the run id is part of the natural key rather than a mutable attribute.
    run_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    # The subscription line the check was about, as the source system named it.
    line_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    # The check that produced this row, e.g. "price_not_propagated".
    check_code: Mapped[str] = mapped_column(String(100), nullable=False)

    expected_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    delta_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)

    # Non-money context the detector wants to keep: quantities, matched rate,
    # the clause it relied on. Never a substitute for the three amounts above.
    details: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        # This constraint is what makes detection idempotent: re-running over
        # unchanged data recomputes the same key and writes nothing new.
        UniqueConstraint(
            "run_id",
            "customer_ref",
            "line_ref",
            "period_start",
            "check_code",
            name="uq_reconciliation_result_run_customer_line_period_check",
        ),
    )


class ChangeEvent(Base, TimestampMixin):
    """A field-level before/after, so a case can answer "what changed?"."""

    __tablename__ = "change_event"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    # Which table and record the change was seen on.
    entity_table: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    # contract | crm | implementation | usage | billing
    source_system: Mapped[str] = mapped_column(String(32), nullable=False)
    observed_at: Mapped[date] = mapped_column(Date, nullable=False)
    # rule | model | human -- who decided this was a change worth recording.
    detected_by: Mapped[str] = mapped_column(
        Enum(
            "rule",
            "model",
            "human",
            name="change_detection_source",
            native_enum=False,
            length=16,
        ),
        nullable=False,
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))


Index("ix_reconciliation_result_run_id", ReconciliationResult.run_id)
Index("ix_reconciliation_result_customer_ref", ReconciliationResult.customer_ref)
Index("ix_reconciliation_result_check_code", ReconciliationResult.check_code)
Index("ix_change_event_customer_ref", ChangeEvent.customer_ref)
Index("ix_change_event_entity", ChangeEvent.entity_table, ChangeEvent.entity_ref)
Index("ix_change_event_observed_at", ChangeEvent.observed_at)

__all__ = ["ChangeEvent", "ReconciliationResult"]
