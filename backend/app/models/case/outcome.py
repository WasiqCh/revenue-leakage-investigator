"""What a human decided, and the registry of legitimate exceptions.

See TICKET-006, ``docs/data-model.md`` and ``docs/case-lifecycle.md``.

Plain-English: the system proposes; a human disposes. ``case_outcome`` records what
actually happened to the money -- recovered, written off, or judged a false
alarm -- and is written once, never edited.

``approved_exception`` is the other half of "is this actually a leak?": the list
of reasons a gap is *legitimate*. A free pilot or an approved discount produces a
gap that looks identical to a bug, so the answer is a lookup against this table
with a date range, not a guess. The confidence engine reads it (see
``docs/confidence.md``, factor ``exception_absence``).
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType

OUTCOME_TYPE = Enum(
    "recovered",
    "partially_recovered",
    "written_off",
    "false_positive",
    "accepted_exception",
    name="outcome_type",
    native_enum=False,
    length=32,
)

EXCEPTION_REASON = Enum(
    "free_pilot",
    "approved_discount",
    "grace_period",
    "grandfathered_rate",
    "contractual_cap",
    "goodwill_credit",
    name="exception_reason",
    native_enum=False,
    length=32,
)


class CaseOutcome(Base, TimestampMixin):
    """What actually happened to the money. Written once, then referenced."""

    __tablename__ = "case_outcome"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    outcome_type: Mapped[str] = mapped_column(OUTCOME_TYPE, nullable=False)

    # How much of the delta actually came back. Null when nothing was recovered.
    recovered_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    written_off_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())

    # The reason code the reviewer picked, and any free-text justification.
    reason_code: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[str | None] = mapped_column(String(255))
    decided_at: Mapped[date | None] = mapped_column(Date)

    # Set when the outcome was driven by an approved_exception row.
    approved_exception_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("approved_exception.id", ondelete="SET NULL")
    )


class ApprovedException(Base, TimestampMixin):
    """The registry of legitimate reasons a gap exists."""

    __tablename__ = "approved_exception"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_line_ref: Mapped[str | None] = mapped_column(String(100))
    product_ref: Mapped[str | None] = mapped_column(String(100))

    reason: Mapped[str] = mapped_column(EXCEPTION_REASON, nullable=False)
    # Half-open in effect: [valid_from, valid_to). Null valid_to means "still open".
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)

    # An optional cap: "the first 5,000 USD of this gap is expected".
    max_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())

    approved_by: Mapped[str | None] = mapped_column(String(255))
    reference: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        # One live exception per customer, line and reason over a given window.
        UniqueConstraint(
            "customer_ref",
            "subscription_line_ref",
            "reason",
            "valid_from",
            name="uq_approved_exception_customer_line_reason_from",
        ),
    )


Index("ix_case_outcome_outcome_type", CaseOutcome.outcome_type)
Index("ix_case_outcome_reason_code", CaseOutcome.reason_code)
Index("ix_approved_exception_customer_ref", ApprovedException.customer_ref)
Index("ix_approved_exception_reason", ApprovedException.reason)
Index("ix_approved_exception_valid_from", ApprovedException.valid_from)
Index("ix_approved_exception_valid_to", ApprovedException.valid_to)

__all__ = ["ApprovedException", "CaseOutcome"]
