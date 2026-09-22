"""The audit trail, and the ground truth the evaluation compares against.

See TICKET-006, ``docs/data-model.md`` and ``docs/adr/ADR-004-read-only-role-guardrail.md``.

Plain-English: ``audit_event`` is the "who changed what, and what was it before?"
log. It is append-only -- TICKET-007 installs a database trigger that raises on
UPDATE and DELETE, so the history cannot be quietly rewritten even by a bug in
our own code.

``golden_label`` is the answer key. Because the scenario generator *injects* the
defect, the right answer is known by construction rather than judged by hand,
which is what makes the evaluation suite in later tickets possible at all.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, Boolean, Date, DateTime, Enum, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType

AUDIT_ACTION = Enum(
    "insert",
    "update",
    "delete",
    "status_change",
    "approval",
    name="audit_action",
    native_enum=False,
    length=32,
)


class AuditEvent(Base, TimestampMixin):
    """Append-only record of every state change. Immutable by trigger (TICKET-007)."""

    __tablename__ = "audit_event"

    # Which table and row changed. No foreign key: audit rows must survive the
    # deletion of the row they describe.
    entity_table: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(AUDIT_ACTION, nullable=False)

    # Who did it: a user, a role, or a named component of the pipeline.
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    # system | human | agent -- recorded so "did a person approve this?" is answerable.
    actor_type: Mapped[str] = mapped_column(
        Enum("system", "human", "agent", name="actor_type", native_enum=False, length=16),
        nullable=False,
    )

    # Before and after, as JSON snapshots. Null before means "created".
    before: Mapped[dict[str, object] | None] = mapped_column(JSON)
    after: Mapped[dict[str, object] | None] = mapped_column(JSON)
    # Which columns changed, so a reviewer does not diff two blobs by eye.
    changed_fields: Mapped[list[str] | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    # The run or job this happened inside, when it happened inside one.
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GoldenLabel(Base, TimestampMixin):
    """The ground-truth answer for a generated scenario. Known by construction."""

    __tablename__ = "golden_label"

    # Which scenario and which detection run this label belongs to.
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    run_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)

    # What the generator injected.
    leak_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_line_ref: Mapped[str | None] = mapped_column(String(100))
    product_ref: Mapped[str | None] = mapped_column(String(100))

    # The window the defect spans, and the money it should have produced.
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    expected_delta_amount: Mapped[Decimal | None] = mapped_column(MoneyType())
    currency: Mapped[str | None] = mapped_column(CurrencyCode())

    # How visible the defect was meant to be, and how many periods it spans -- a
    # five-month drift and a one-month slip are not equally hard to find.
    severity: Mapped[str | None] = mapped_column(String(32))
    expected_period_count: Mapped[int | None] = mapped_column(Integer)
    # True when the correct answer is "no leak here" -- the false-positive check.
    is_benign: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text)


Index("ix_audit_event_entity", AuditEvent.entity_table, AuditEvent.entity_id)
Index("ix_audit_event_actor", AuditEvent.actor)
Index("ix_audit_event_occurred_at", AuditEvent.occurred_at)
Index("ix_golden_label_scenario_id", GoldenLabel.scenario_id)
Index("ix_golden_label_customer_ref", GoldenLabel.customer_ref)
Index("ix_golden_label_leak_type", GoldenLabel.leak_type)

__all__ = ["AuditEvent", "GoldenLabel"]
