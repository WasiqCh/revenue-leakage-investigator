"""Columns shared by every source table. See TICKET-005.

Plain-English: every row we ingest carries two things beyond its own fields --
which system it came from, and what that system called it. Together those form
the row's **natural key**: the business fact that makes two rows the same row.
Writers upsert on it, which is what makes re-running an ingestion idempotent
instead of duplicating everything. See ``docs/data-model.md``, "Keys and
idempotency".
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db.enums import SourceSystem

SOURCE_SYSTEM_COLUMN = Enum(
    SourceSystem,
    name="source_system",
    native_enum=False,
    length=32,
    # Store the readable value ("contract"), not the Python member name.
    values_callable=lambda enum: [member.value for member in enum],
)


class SourceNaturalKeyMixin:
    """Adds ``source_system``, ``source_id`` and the unique constraint on both."""

    @declared_attr
    def source_system(cls) -> Mapped[SourceSystem]:
        return mapped_column(SOURCE_SYSTEM_COLUMN, nullable=False)

    @declared_attr
    def source_id(cls) -> Mapped[str]:
        return mapped_column(String(255), nullable=False)

    # `declared_attr.directive`, not plain `declared_attr`: this is a
    # table-level option rather than a mapped column, and mypy's SQLAlchemy
    # plugin rejects the plain form here.
    @declared_attr.directive
    def __table_args__(cls) -> tuple[Any, ...]:
        table_name: str = cls.__dict__["__tablename__"]
        return (
            UniqueConstraint(
                "source_system",
                "source_id",
                name=f"uq_{table_name}_source_natural_key",
            ),
        )
