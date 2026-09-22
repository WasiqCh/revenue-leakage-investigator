"""The canonical product, its other SKUs, the prices that may apply, and FX.

See TICKET-005 and ``docs/data-model.md``.

Plain-English: the same product is sold under different SKUs over time, and the
price that applies depends on a list, a volume tier, a contract override or a
promotion. ``pricing_rule`` keeps every candidate price with a priority, so the
resolution is a deterministic lookup rather than a judgement call.
``fx_rate`` is the only place a conversion factor may come from -- no code is
allowed to invent one.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType
from app.models.source.common import SourceNaturalKeyMixin


class Product(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The canonical product: SKU, unit of measure and list price."""

    __tablename__ = "product"

    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    list_price: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)


class ProductAlias(SourceNaturalKeyMixin, Base, TimestampMixin):
    """A historical or per-system SKU that maps onto a canonical product."""

    __tablename__ = "product_alias"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    alias_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    # Which system uses this spelling, and how sure entity resolution was.
    alias_source: Mapped[str] = mapped_column(String(32), nullable=False)
    match_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)


class PricingRule(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One candidate price, with the priority that decides which one wins."""

    __tablename__ = "pricing_rule"

    product_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE")
    )
    # list | tiered | volume | contract_override | promo
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Lower number wins. Equal priority is broken by specificity.
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    # How narrowly the rule is scoped: customer + product beats product alone.
    specificity: Mapped[int] = mapped_column(Integer, nullable=False)
    customer_ref: Mapped[str | None] = mapped_column(String(100))
    min_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    max_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4))
    unit_price: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_to: Mapped[date | None] = mapped_column(Date)


class FxRate(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One exchange rate for one currency pair on one date.

    The natural key is the pair plus the date -- a rate is only meaningful on the
    day it applied, which is why the pair alone is not unique.
    """

    __tablename__ = "fx_rate"

    base_currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    quote_currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)

    # Declaring __table_args__ here replaces the mixin's, so both constraints
    # have to be listed: the source natural key, and the documented business key.
    __table_args__ = (
        UniqueConstraint("source_system", "source_id", name="uq_fx_rate_source_natural_key"),
        UniqueConstraint(
            "base_currency",
            "quote_currency",
            "as_of_date",
            name="uq_fx_rate_pair_as_of_date",
        ),
    )


# Price resolution walks product -> aliases -> candidate rules, so both the
# alias lookup and the rule lookup are indexed.
Index("ix_product_alias_product_id", ProductAlias.product_id)
Index("ix_product_alias_alias_sku", ProductAlias.alias_sku)
Index("ix_pricing_rule_product_id", PricingRule.product_id)
Index("ix_pricing_rule_customer_ref", PricingRule.customer_ref)

__all__ = ["FxRate", "PricingRule", "Product", "ProductAlias"]
