"""What the product actually recorded. See TICKET-005.

Plain-English: usage is the "consumption" side. A customer may be subscribed to
100 seats and use 140, or be billed for a flat fee while metering says they blew
past a tier. ``usage_snapshot`` is the record that makes "billed for less than
they used" provable.

Its natural key is the customer, product, metric and period start -- the same
measurement for the same period is the same row, so re-ingesting is idempotent.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.source.common import SourceNaturalKeyMixin


class UsageSnapshot(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One measurement of one metric for one customer, product and period."""

    __tablename__ = "usage_snapshot"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    product_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    # seats | api_calls | gb_storage | active_users
    metric: Mapped[str] = mapped_column(String(50), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    # When the product recorded it, which is not always when it happened.
    recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    # Declaring __table_args__ replaces the mixin's, so both keys are listed:
    # the source natural key and the documented business key.
    __table_args__ = (
        UniqueConstraint("source_system", "source_id", name="uq_usage_snapshot_source_natural_key"),
        UniqueConstraint(
            "customer_ref",
            "product_ref",
            "metric",
            "period_start",
            name="uq_usage_snapshot_customer_product_metric_period",
        ),
    )


# The business key above already indexes customer -> product -> metric, so the
# extra index is for the other direction: "everything measured in this period".
Index("ix_usage_snapshot_period_start", UsageSnapshot.period_start)

__all__ = ["UsageSnapshot"]
