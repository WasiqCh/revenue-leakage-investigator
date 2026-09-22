"""The derived, case and ops schema, as the database actually has it. See TICKET-006.

Plain-English: TICKET-005 proved the tables the outside systems feed us exist.
This proves the tables *we* write exist, that the two uniqueness rules hold under
a real INSERT, and that the vector index is genuinely used -- not merely created.

The last point is the one worth arguing about. An index that exists but is never
chosen by the planner is worse than no index, because it costs writes and buys
nothing. So the test asks Postgres for its plan and reads the answer, rather than
trusting that "we created an index" implies "queries use it".
"""

from __future__ import annotations

import random
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.config import get_settings, settings_or_none
from app.db.base import Base
from app.db.engine import to_psycopg_dsn
from app.models import case, derived, ops, source  # noqa: F401  -- registers every table

# The 21 tables TICKET-006 adds, per docs/tickets/TICKET-006.
EXPECTED_TABLES = {
    "agent_trace_step",
    "approved_exception",
    "audit_event",
    "billing_period",
    "case",
    "case_outcome",
    "case_period",
    "change_event",
    "entity_resolution_match",
    "eval_result",
    "eval_run",
    "evidence",
    "golden_label",
    "investigation_report",
    "investigation_run",
    "job",
    "llm_call",
    "qa_message",
    "recommendation",
    "reconciliation_result",
    "reconciliation_run",
}

# backend/tests/integration/test_schema_derived.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Enough rows that a sequential scan is genuinely more expensive than the index,
# so the planner's choice means something. Clauses are ~6 KB of vector each, so
# this stays modest for a test database while crossing the HNSW planner threshold.
PROBE_ROWS = 2_500
PROBE_SEED = 20260922
PROBE_SOURCE_ID_PREFIX = "vector-index-probe-"
PROBE_SOURCE_SYSTEM = "contract"

# CAST(...) rather than ':x::vector': SQLAlchemy will not treat a bind parameter
# that is immediately followed by a colon as a parameter at all, so the cast form
# is what actually sends the value.
INSERT_CLAUSE = text(
    "INSERT INTO contract_clause "
    "(contract_ref, clause_type, char_start, char_end, text, embedding, "
    " source_system, source_id) "
    "VALUES ('CON-PROBE', 'price_uplift', 0, 10, 'probe', CAST(:embedding AS vector), "
    " :source_system, :source_id)"
)

# Cosine distance, matching the vector_cosine_ops index we asked for.
EXPLAIN_VECTOR_QUERY = text(
    "EXPLAIN SELECT id FROM contract_clause ORDER BY embedding <=> CAST(:probe AS vector) LIMIT 5"
)


def _sync_engine():
    return create_engine(to_psycopg_dsn(get_settings().database_url), future=True)


@pytest.fixture(scope="module")
def engine():
    if settings_or_none() is None:
        pytest.skip("no database is configured, so there is no database to inspect")
    engine = _sync_engine()
    yield engine
    engine.dispose()


def _probe_vector(rng: random.Random, dimensions: int = 1536) -> str:
    """A random vector as the text form pgvector accepts: '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{rng.random():.6f}" for _ in range(dimensions)) + "]"


def test_derived_case_and_ops_tables_exist_in_the_database(engine) -> None:
    """Every table the ticket names must be in Postgres, not just in the models."""
    assert EXPECTED_TABLES <= set(Base.metadata.tables)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "AND table_name <> 'alembic_version'"  # Alembic's own bookkeeping.
            )
        ).fetchall()

    assert EXPECTED_TABLES <= {row[0] for row in rows}


def test_metadata_and_database_agree_with_no_drift(engine) -> None:
    """Nothing in the models is missing, and nothing stray is in the database."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "AND table_name <> 'alembic_version'"
            )
        ).fetchall()

    assert {row[0] for row in rows} == set(Base.metadata.tables)


def test_case_key_is_unique(engine) -> None:
    """Acceptance criterion 2: one fingerprint, one row, however often we re-run."""
    insert = text(
        'INSERT INTO "case" '
        "(case_key, fingerprint_version, customer_ref, leak_type, status, "
        " expected_amount, actual_amount, delta_amount, currency) "
        "VALUES (:case_key, 1, 'CUST-1', 'price_not_propagated', 'open', "
        " 100.0000, 80.0000, 20.0000, 'USD')"
    )
    params = {"case_key": "case-key-uniqueness-probe"}

    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(insert, params)
        with pytest.raises(IntegrityError):
            connection.execute(insert, params)
        # Rolling back removes both rows, so the probe leaves nothing behind.
        transaction.rollback()


def test_reconciliation_result_natural_key_is_unique(engine) -> None:
    """Acceptance criterion 3, checked by a real INSERT rather than by reading DDL.

    The key is (run_id, customer, line, period, check_code). Re-running detection
    over unchanged data must collide, not append.
    """
    run_id = uuid.uuid4()
    insert = text(
        "INSERT INTO reconciliation_result "
        "(run_id, customer_ref, line_ref, period_start, period_end, check_code, "
        " expected_amount, actual_amount, delta_amount, currency) "
        "VALUES (:run_id, 'CUST-1', 'LINE-1', DATE '2026-01-01', DATE '2026-02-01', "
        " 'price_not_propagated', 100.0000, 80.0000, 20.0000, 'USD')"
    )
    params = {"run_id": run_id}

    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(insert, params)
        with pytest.raises(IntegrityError):
            connection.execute(insert, params)
        transaction.rollback()

    # The same check in a different run is a different row -- runs coexist.
    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(insert, {"run_id": uuid.uuid4()})
        transaction.rollback()


def test_vector_and_full_text_indexes_exist_with_the_right_method(engine) -> None:
    """The index has to be an HNSW one on cosine distance, and GIN on the tsv."""
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'contract_clause'")
        ).fetchall()

    definitions = {row[0]: row[1] for row in rows}

    assert "ix_contract_clause_embedding" in definitions
    assert "USING hnsw" in definitions["ix_contract_clause_embedding"]
    assert "vector_cosine_ops" in definitions["ix_contract_clause_embedding"]

    assert "ix_contract_clause_tsv" in definitions
    assert "USING gin" in definitions["ix_contract_clause_tsv"]


def test_explain_uses_the_vector_index(engine) -> None:
    """Acceptance criterion 4: the planner picks the index, unprompted.

    No planner hints are set here. The only thing that makes the index win is
    that a sequential scan over a few hundred wide rows genuinely costs more.
    """
    rng = random.Random(PROBE_SEED)

    with engine.connect() as connection, connection.begin() as transaction:
        for index in range(PROBE_ROWS):
            connection.execute(
                INSERT_CLAUSE,
                {
                    "embedding": _probe_vector(rng),
                    "source_system": PROBE_SOURCE_SYSTEM,
                    "source_id": f"{PROBE_SOURCE_ID_PREFIX}{index}",
                },
            )
        # Without statistics the planner guesses, and a guess is not evidence.
        connection.execute(text("ANALYZE contract_clause"))

        plan = "\n".join(
            row[0]
            for row in connection.execute(
                EXPLAIN_VECTOR_QUERY, {"probe": _probe_vector(rng)}
            ).fetchall()
        )
        transaction.rollback()

    assert "ix_contract_clause_embedding" in plan, f"planner ignored the index:\n{plan}"
    assert "Index Scan" in plan, f"no index scan in the plan:\n{plan}"


def test_derived_migration_up_down_up_succeeds() -> None:
    """Acceptance criterion 1: this revision is reversible, not merely applicable.

    Runs last and leaves the database migrated.
    """
    if settings_or_none() is None:
        pytest.skip("no database is configured, so there is no database to migrate")

    for args in (("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"alembic {' '.join(args)} failed:\n{result.stderr}"


def test_money_columns_in_the_new_tables_are_exact(engine) -> None:
    """Money in the new tables obeys the same rule as money everywhere: no floats."""
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT data_type, numeric_precision, numeric_scale "
                "FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'case' "
                "AND column_name = 'delta_amount'"
            )
        ).one()

    assert row.data_type == "numeric"
    assert (row.numeric_precision, row.numeric_scale) == (20, 4)

    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(
            text(
                'INSERT INTO "case" '
                "(case_key, fingerprint_version, customer_ref, leak_type, status, "
                " expected_amount, actual_amount, delta_amount, currency) "
                "VALUES ('money-round-trip-probe', 1, 'CUST-1', 'period_gap', 'open', "
                " :amount, 0.0000, :amount, 'USD')"
            ),
            {"amount": Decimal("98765.4321")},
        )
        stored = connection.execute(
            text("SELECT delta_amount FROM \"case\" WHERE case_key = 'money-round-trip-probe'")
        ).scalar_one()
        transaction.rollback()

    assert isinstance(stored, Decimal)
    assert stored == Decimal("98765.4321")
