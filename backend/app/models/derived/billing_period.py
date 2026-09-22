"""The materialised billing periods a subscription is charged over.

See TICKET-006 and ``docs/billing-periods.md``.

Plain-English: a subscription says "monthly from the 4th", and this table turns
that sentence into the actual list of periods -- one row per month, each a
half-open ``[start, end)`` range. Adjacent periods share a boundary date and
never both count it, which is why the range is half-open rather than two loose
dates.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, HalfOpenDateInterval, HalfOpenInterval, MoneyType


class BillingPeriod(Base, TimestampMixin):
    """One period a subscription is billed over, with proration metadata."""

    __tablename__ = "billing_period"

    # Which subscription and line this period belongs to, as the source systems
    # named them. See the note in app.models.source.__init__ about reference
    # strings: identity is resolved later, in entity resolution.
    subscription_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_line_ref: Mapped[str | None] = mapped_column(String(100))
    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    product_ref: Mapped[str | None] = mapped_column(String(100))

    # 0-based position in the subscription's period sequence. Part of the
    # natural key, so re-enumerating the same subscription writes zero new rows.
    period_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # The half-open interval itself: [lower, upper).
    period: Mapped[HalfOpenInterval] = mapped_column(HalfOpenDateInterval(), nullable=False)

    days_in_period: Mapped[int | None] = mapped_column(Integer)
    # A period that does not cover a full cycle -- the first month after a
    # mid-cycle start, or a cancellation -- carries the fraction that applies.
    is_partial: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    proration_factor: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))

    currency: Mapped[str | None] = mapped_column(CurrencyCode())
    expected_amount: Mapped[Decimal | None] = mapped_column(MoneyType())

    __table_args__ = (
        UniqueConstraint(
            "subscription_ref",
            "period_index",
            name="uq_billing_period_subscription_period_index",
        ),
    )


Index("ix_billing_period_subscription_ref", BillingPeriod.subscription_ref)
Index("ix_billing_period_customer_ref", BillingPeriod.customer_ref)
# Period lookups are almost always "the period containing this date".
Index("ix_billing_period_period", BillingPeriod.period)
Index("ix_billing_period_period_index", BillingPeriod.period_index)

__all__ = ["BillingPeriod"]
