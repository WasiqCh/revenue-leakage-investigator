"""What the CRM says is subscribed, and whether it actually went live.

See TICKET-005 and ``docs/data-model.md``.

Plain-English: ``subscription`` is the promise ("they are on the Enterprise plan,
billed monthly from the 1st") and ``implementation`` is the reality ("they went
live three weeks late"). Billing often starts on the promise, so the difference
between the two dates is a recurring source of leakage.

``subscription_line`` is SCD-2: a price or quantity change closes the old row and
opens a new one instead of overwriting it, so "what were they subscribed to in
March?" stays answerable.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType
from app.models.source.common import SourceNaturalKeyMixin


class Subscription(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The subscription header, including the billing anchor that drives periods."""

    __tablename__ = "subscription"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_ref: Mapped[str | None] = mapped_column(String(100))
    subscription_number: Mapped[str] = mapped_column(String(100), nullable=False)
    # active | suspended | cancelled | pending
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    # monthly | quarterly | annual
    billing_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    # The day the billing cycle is anchored to. Period enumeration starts here
    # rather than on the 1st of a month. See docs/billing-periods.md.
    billing_anchor_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)


class SubscriptionLine(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One product/quantity/price row inside a subscription. SCD-2.

    ``valid_from``/``valid_to`` are the row's own lifetime: a change closes the
    previous row by setting ``valid_to`` and opens a new one. ``is_current`` is
    the shortcut for "the row that applies now".
    """

    __tablename__ = "subscription_line"

    subscription_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    line_number: Mapped[int | None] = mapped_column(Integer)
    product_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Implementation(SourceNaturalKeyMixin, Base, TimestampMixin):
    """Go-live and actual activation dates, and the onboarding fee charged."""

    __tablename__ = "implementation"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_ref: Mapped[str | None] = mapped_column(String(100))
    project_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    # scheduled | in_progress | live | stalled
    status: Mapped[str | None] = mapped_column(String(50))
    go_live_date: Mapped[date | None] = mapped_column(Date)
    actual_activation_date: Mapped[date | None] = mapped_column(Date)
    onboarding_fee: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())
    services_delivered: Mapped[dict[str, object] | None] = mapped_column(JSON)


# Period enumeration and proration read these per subscription, per line and
# per date, so the subscription reference and the SCD-2 "current row" flag are
# indexed alongside the customer.
Index("ix_subscription_customer_ref", Subscription.customer_ref)
Index("ix_subscription_subscription_number", Subscription.subscription_number)
Index("ix_subscription_line_subscription_ref", SubscriptionLine.subscription_ref)
Index("ix_subscription_line_product_ref", SubscriptionLine.product_ref)
Index("ix_subscription_line_is_current", SubscriptionLine.is_current)
Index("ix_implementation_customer_ref", Implementation.customer_ref)
Index("ix_implementation_subscription_ref", Implementation.subscription_ref)

__all__ = ["Implementation", "Subscription", "SubscriptionLine"]
