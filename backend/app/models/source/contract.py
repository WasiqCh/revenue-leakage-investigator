"""Contracts, their clauses, the terms extracted from them, and amendments.

See TICKET-005 and ``docs/data-model.md``.

Plain-English: this is where most leakage is born. A contract says one price, an
amendment changes it, and the change never reaches billing. So the amendment is
stored as a before/after pair (``amendment_term``) rather than as a restated
contract, because "what changed" is exactly the question an investigation asks.

``contract_clause`` holds the text split into clauses, with both a semantic
vector and a full-text vector so retrieval can run a semantic and a lexical
search and fuse the results. The indexes on those two columns are created in
TICKET-006, which owns the proof that they are used.
"""

# ---------------------------------------------------------------------------
# The two retrieval indexes. See TICKET-006 and docs/retrieval.md.
#
# HNSW rather than IVFFlat: it can be built on an empty table, needs no
# pre-training step, and stays accurate as rows are inserted -- which matters
# because clauses are embedded incrementally by a job, not loaded in one batch.
# ``vector_cosine_ops`` matches the distance function retrieval uses, so the
# index is actually eligible for the query EXPLAIN has to prove.
#
# 1536 dimensions is comfortably under pgvector's 2000-dimension index limit.
# ---------------------------------------------------------------------------

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.types import CurrencyCode, MoneyType
from app.models.source.common import SourceNaturalKeyMixin

# Clause embedding width. Hard-coded on purpose: a column's width is part of the
# schema, so it must not shift with an environment variable -- that would make
# two databases disagree about the same migration. It has to match
# Settings.embedding_dimensions, and a test asserts they agree. 1536 is the
# documented default and stays well under pgvector's 2000-dimension index limit.
EMBEDDING_DIMENSIONS = 1536


class Contract(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The agreement's commercial header, plus the raw payload as received."""

    __tablename__ = "contract"

    customer_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_number: Mapped[str] = mapped_column(String(100), nullable=False)
    # draft | active | expired | terminated | superseded
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    currency: Mapped[str] = mapped_column(CurrencyCode(), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    signed_date: Mapped[date | None] = mapped_column(Date)
    term_months: Mapped[int | None] = mapped_column(Integer)
    # auto_renew | manual | none
    renewal_type: Mapped[str | None] = mapped_column(String(50))
    notice_period_days: Mapped[int | None] = mapped_column(Integer)
    # monthly | quarterly | annual
    billing_frequency: Mapped[str | None] = mapped_column(String(50))
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)


class ContractClause(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One clause of a contract: its text, its span, and both search vectors."""

    __tablename__ = "contract_clause"

    contract_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    # price_uplift | discount | termination | minimum_commitment | payment_terms
    clause_type: Mapped[str] = mapped_column(String(50), nullable=False)
    clause_number: Mapped[str | None] = mapped_column(String(50))
    # Character offsets into the contract text, so a citation can be re-fetched
    # exactly rather than re-found.
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Lexical search vector; TICKET-006 adds the GIN index.
    tsv: Mapped[str | None] = mapped_column(TSVECTOR)
    # Semantic search vector; TICKET-006 adds the pgvector index.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))


class ContractTerm(SourceNaturalKeyMixin, Base, TimestampMixin):
    """One extracted term -- base price, uplift cap, minimum commitment.

    Marked SRC/DERIV in the data model: the value comes out of contract prose
    rather than a system field, so ``extraction_method`` records whether a rule,
    the model or a human produced it.
    """

    __tablename__ = "contract_term"

    contract_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    source_clause_ref: Mapped[str | None] = mapped_column(String(100))
    # base_price | notice_period | uplift_cap | minimum_commitment | discount
    term_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value_numeric: Mapped[Decimal | None] = mapped_column(MoneyType())
    value_text: Mapped[str | None] = mapped_column(String(255))
    currency: Mapped[str | None] = mapped_column(CurrencyCode())
    # rule | model | human
    extraction_method: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class Amendment(SourceNaturalKeyMixin, Base, TimestampMixin):
    """A change order against a contract."""

    __tablename__ = "amendment"

    contract_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    amendment_number: Mapped[str] = mapped_column(String(100), nullable=False)
    # price_change | quantity_change | term_change | product_swap
    change_type: Mapped[str | None] = mapped_column(String(50))
    # draft | signed | applied | missed
    status: Mapped[str | None] = mapped_column(String(50))
    signed_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)


class AmendmentTerm(SourceNaturalKeyMixin, Base, TimestampMixin):
    """The before/after values an amendment changes.

    This pair is the evidence for "amendment not propagated": the contract says
    X, billing still charges the old value, and this row is where the difference
    is documented.
    """

    __tablename__ = "amendment_term"

    amendment_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    term_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(255))
    new_value: Mapped[str | None] = mapped_column(String(255))
    effective_date: Mapped[date | None] = mapped_column(Date)


# An investigation always starts from a contract and walks down to its clauses,
# terms and amendments, so the parent reference on each child is indexed.
Index("ix_contract_customer_ref", Contract.customer_ref)
Index("ix_contract_contract_number", Contract.contract_number)
Index("ix_contract_clause_contract_ref", ContractClause.contract_ref)
Index("ix_contract_clause_clause_type", ContractClause.clause_type)
# Semantic search: nearest neighbour over clause embeddings.
Index(
    "ix_contract_clause_embedding",
    ContractClause.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": "16", "ef_construction": "64"},
    postgresql_ops={"embedding": "vector_cosine_ops"},
)
# Lexical search: full-text match over the same clause text.
Index("ix_contract_clause_tsv", ContractClause.tsv, postgresql_using="gin")
Index("ix_contract_term_contract_ref", ContractTerm.contract_ref)
Index("ix_contract_term_term_type", ContractTerm.term_type)
Index("ix_amendment_contract_ref", Amendment.contract_ref)
Index("ix_amendment_term_amendment_ref", AmendmentTerm.amendment_ref)

__all__ = [
    "Amendment",
    "AmendmentTerm",
    "Contract",
    "ContractClause",
    "ContractTerm",
]
