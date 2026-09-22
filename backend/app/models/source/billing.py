"""Invoices, invoice lines and credit memos -- what billing actually charged.

See TICKET-005 and ``docs/data-model.md``.

Plain-English: this is the "actual" side of every reconciliation. The contract
and subscription say what should have been charged; these tables say what was.
The gap between the two is what the whole product looks for.

``invoice_line`` carries the **service period**, and that column is the whole
reason proration bugs are detectable: if a line is billed for a period that does
not match the billing period the subscription defines, the mismatch is visible
as data rather than as an argument.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import JSON, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType
from app.models.source.common import SourceNaturalKeyMixin


class Invoice(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The billing system's invoice header. Insert-only once ingested."""

    __tablename__ = "invoice"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    # draft | issued | paid | void | overdue
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    # The span the invoice covers, independent of the line-level service periods.
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    subtotal: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    tax: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    total: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)


class InvoiceLine(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One billed line, with the service period proration is checked against."""

    __tablename__ = "invoice_line"

    invoice_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    line_number: Mapped[int | None] = mapped_column(Integer)
    product_ref: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    service_period_start: Mapped[date | None] = mapped_column(Date)
    service_period_end: Mapped[date | None] = mapped_column(Date)


class CreditMemo(SourceNaturalKeyMixin, Base, TimestampMixin):
    """Money credited back. Nets off actual billed, and evidences recovery."""

    __tablename__ = "credit_memo"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_ref: Mapped[str | None] = mapped_column(String(100))
    credit_memo_number: Mapped[str] = mapped_column(String(100), nullable=False)
    # billing_error | goodwill | service_credit | cancellation
    reason: Mapped[str | None] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(MoneyType(), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    issue_date: Mapped[date | None] = mapped_column(Date)


# "What was billed for this customer over this span" is the question every
# detector asks, so the customer, the invoice and the service period are indexed.
Index("ix_invoice_customer_ref", Invoice.customer_ref)
Index("ix_invoice_invoice_number", Invoice.invoice_number)
Index("ix_invoice_period_start", Invoice.period_start)
Index("ix_invoice_line_invoice_ref", InvoiceLine.invoice_ref)
Index("ix_invoice_line_product_ref", InvoiceLine.product_ref)
Index("ix_invoice_line_service_period_start", InvoiceLine.service_period_start)
Index("ix_credit_memo_customer_ref", CreditMemo.customer_ref)
Index("ix_credit_memo_invoice_ref", CreditMemo.invoice_ref)

__all__ = ["CreditMemo", "Invoice", "InvoiceLine"]
