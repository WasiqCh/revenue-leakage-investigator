"""What supports a case, and what we propose should be done about it.

See TICKET-006 and ``docs/data-model.md``.

Plain-English: ``evidence`` is a citable fact -- it points at a real row in a real
source table and carries the exact excerpt shown to a reviewer. A claim with no
evidence row behind it does not survive verification.

``recommendation`` is a proposal only. Nothing in this system executes one; a
human approves it in the target system.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType

APPROVAL_STATE = Enum(
    "proposed",
    "approved",
    "rejected",
    "executed",
    name="approval_state",
    native_enum=False,
    length=32,
)


class Evidence(Base, TimestampMixin):
    """A citable fact tied to a real source row."""

    __tablename__ = "evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    # Which table and row this came from. Stored as table + source id so the
    # verifier can re-fetch the exact text rather than trust a summary.
    source_table: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    # The label shown in the interface, e.g. "Contract clause 7.2 (price uplift)".
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    # Structured extras: character span, clause number, invoice line number.
    citation: Mapped[dict[str, object] | None] = mapped_column(JSONB)


class Recommendation(Base, TimestampMixin):
    """The proposed correction. A proposal only -- never executed here."""

    __tablename__ = "recommendation"

    case_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("case.id", ondelete="CASCADE"), nullable=False
    )
    # contract | crm | implementation | usage | billing
    target_system: Mapped[str] = mapped_column(String(32), nullable=False)
    target_record_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g. reprice_line | issue_credit_memo | correct_quantity
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())
    rationale: Mapped[str | None] = mapped_column(Text)
    approval_state: Mapped[str] = mapped_column(APPROVAL_STATE, nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(255))


Index("ix_evidence_case_id", Evidence.case_id)
Index("ix_evidence_source", Evidence.source_table, Evidence.source_id)
Index("ix_recommendation_case_id", Recommendation.case_id)
Index("ix_recommendation_approval_state", Recommendation.approval_state)

__all__ = ["Evidence", "Recommendation"]
