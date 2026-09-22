"""A record of every matching decision between two references.

See TICKET-006 and ``docs/data-model.md``.

Plain-English: "ACME INC" on an invoice and "Acme Ltd" in the CRM are the same
company -- but that is a *decision*, not a fact. This table records the decision,
how confident it was, and whether a human confirmed or rejected it. That is what
lets us re-run resolution without silently changing the answer.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Enum, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin

MATCH_METHOD = Enum(
    "exact",
    "normalised",
    "fuzzy",
    "domain",
    "manual",
    name="match_method",
    native_enum=False,
    length=32,
)

MATCH_DECISION = Enum(
    "auto_matched",
    "human_confirmed",
    "human_rejected",
    name="match_decision",
    native_enum=False,
    length=32,
)


class EntityResolutionMatch(Base, TimestampMixin):
    """One matching decision between two references."""

    __tablename__ = "entity_resolution_match"

    # customer | product
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    # The two sides of the comparison, each identified by system + reference.
    left_system: Mapped[str] = mapped_column(String(32), nullable=False)
    left_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    right_system: Mapped[str] = mapped_column(String(32), nullable=False)
    right_ref: Mapped[str] = mapped_column(String(255), nullable=False)

    method: Mapped[str] = mapped_column(MATCH_METHOD, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    decision: Mapped[str] = mapped_column(MATCH_DECISION, nullable=False)
    # Who confirmed or rejected it, when the decision was not automatic.
    decided_by: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "left_system",
            "left_ref",
            "right_system",
            "right_ref",
            name="uq_entity_resolution_match_pair",
        ),
    )


Index(
    "ix_entity_resolution_match_left",
    EntityResolutionMatch.left_system,
    EntityResolutionMatch.left_ref,
)
Index(
    "ix_entity_resolution_match_right",
    EntityResolutionMatch.right_system,
    EntityResolutionMatch.right_ref,
)
Index("ix_entity_resolution_match_decision", EntityResolutionMatch.decision)

__all__ = ["EntityResolutionMatch"]
