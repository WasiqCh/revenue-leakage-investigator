"""The resolved customer, every name it goes by, and what sales recorded.

See TICKET-005 and ``docs/data-model.md``.

Plain-English: one company may appear as "Acme Ltd" in the CRM, "ACME INC" on an
invoice and "Acme" in the product. ``customer`` is the single row we decide they
all mean; ``customer_alias`` keeps the other spellings so a later import can
still recognise them. ``crm_opportunity`` is what sales believed about the deal,
which is often different from what was actually contracted -- that gap is
itself a source of leakage.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Date, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType
from app.models.source.common import SourceNaturalKeyMixin


class Customer(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The canonical customer. Identity lives here; other names are aliases."""

    __tablename__ = "customer"

    # The identifier we show everywhere. Kept separate from `id` because it is
    # human-readable and comes from the source system of record.
    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(2))
    industry: Mapped[str | None] = mapped_column(String(100))
    account_owner: Mapped[str | None] = mapped_column(String(255))


class CustomerAlias(SourceNaturalKeyMixin, Base, TimestampMixin):
    """Another spelling of a customer, as used by one system."""

    __tablename__ = "customer_alias"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"), nullable=False
    )
    alias_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # How sure entity resolution was. 1.0 means a human confirmed it.
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)


class CrmOpportunity(SourceNaturalKeyMixin, Base, TimestampMixin):
    """What the CRM says about the deal. Never corrected, even when wrong."""

    __tablename__ = "crm_opportunity"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    opportunity_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    # Stored as a fraction: 0.150000 means 15%.
    discount_pct: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    close_date: Mapped[date | None] = mapped_column(Date)
    owner: Mapped[str | None] = mapped_column(String(255))
    # The untouched payload from the CRM, so nothing is lost by modelling it.
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(
        JSON().with_variant(JSON(), "postgresql")
    )


# Every lookup these tables serve is "find the rows for this customer" or "find
# the row this name belongs to", so those are the columns that get indexes.
Index("ix_customer_alias_customer_id", CustomerAlias.customer_id)
Index("ix_customer_alias_alias_name", CustomerAlias.alias_name)
Index("ix_crm_opportunity_customer_ref", CrmOpportunity.customer_ref)
Index("ix_crm_opportunity_opportunity_ref", CrmOpportunity.opportunity_ref)

__all__ = ["CrmOpportunity", "Customer", "CustomerAlias"]
