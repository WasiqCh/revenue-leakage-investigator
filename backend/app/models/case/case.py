"""The suspected discrepancy itself, and the periods it covers.

See TICKET-006, ``docs/data-model.md`` and ``docs/case-lifecycle.md``.

Plain-English: a case is one problem, not one month of a problem. Five months of
the same under-billing is a single case with five periods attached. That is
enforced structurally: ``case_key`` is hashed from the customer, line, leak type
and product and **excludes the billing period**, so a new mismatching month
extends the case instead of creating a second one.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.enums import CaseStatus, ConfidenceBand
from app.db.types import CurrencyCode, MoneyType

CASE_STATUS = Enum(
    CaseStatus,
    name="case_status",
    native_enum=False,
    length=32,
    values_callable=lambda enum: [member.value for member in enum],
)

CONFIDENCE_BAND = Enum(
    ConfidenceBand,
    name="confidence_band",
    native_enum=False,
    length=16,
    values_callable=lambda enum: [member.value for member in enum],
)


class Case(Base, TimestampMixin):
    """One persistent mismatch, deduplicated across periods."""

    __tablename__ = "case"

    # The fingerprint. Deliberately excludes the period -- see the module note.
    case_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    # Bumped if the fingerprint formula ever changes, so old keys are not
    # silently reinterpreted as new ones.
    fingerprint_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_line_ref: Mapped[str | None] = mapped_column(String(100))
    product_ref: Mapped[str | None] = mapped_column(String(100))
    # e.g. price_not_propagated | usage_unbilled | period_gap | discount_not_applied
    leak_type: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[CaseStatus] = mapped_column(CASE_STATUS, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(32))

    expected_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    actual_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    delta_amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)

    # Written only by the confidence module -- AGENTS.md, "A single writer owns
    # the confidence score". A test in TICKET-021 enforces that.
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    confidence_band: Mapped[ConfidenceBand | None] = mapped_column(CONFIDENCE_BAND)

    # The range the case has been seen over. A new period widens these.
    first_period_start: Mapped[date | None] = mapped_column(Date)
    last_period_end: Mapped[date | None] = mapped_column(Date)


class CasePeriod(Base, TimestampMixin):
    """One billing period a case covers. Five months = five rows, one case."""

    __tablename__ = "case_period"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    expected_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    actual_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    delta_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())


Index("ix_case_customer_ref", Case.customer_ref)
Index("ix_case_leak_type", Case.leak_type)
Index("ix_case_status", Case.status)
Index("ix_case_period_case_id", CasePeriod.case_id)
Index("ix_case_period_start", CasePeriod.period_start)

__all__ = ["Case", "CasePeriod"]
