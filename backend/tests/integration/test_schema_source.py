"""The source-domain schema, as the database actually has it. See TICKET-005.

Plain-English: these tests read the live database rather than the Python classes,
because a model that exists in code but not in Postgres is exactly the mistake
that bites three tickets later. The table set is therefore asserted **exactly** --
a missing table fails, and so does a stray one.
"""

from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from app.config import get_settings, settings_or_none
from app.db.base import Base
from app.db.engine import to_psycopg_dsn
from app.models import source  # noqa: F401  -- registers every table on the metadata
from app.models.source.contract import EMBEDDING_DIMENSIONS

# The 19 tables TICKET-005 names. Kept as a literal on purpose: if someone adds a
# table without adding a migration, this test is what notices.
EXPECTED_TABLES = {
    "amendment",
    "amendment_term",
    "contract",
    "contract_clause",
    "contract_term",
    "credit_memo",
    "crm_opportunity",
    "customer",
    "customer_alias",
    "fx_rate",
    "implementation",
    "invoice",
    "invoice_line",
    "pricing_rule",
    "product",
    "product_alias",
    "subscription",
    "subscription_line",
    "usage_snapshot",
}

AUDIT_COLUMNS = {"id", "created_at", "updated_at"}

# backend/tests/integration/test_schema_source.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _sync_engine():
    return create_engine(to_psycopg_dsn(get_settings().database_url), future=True)


@pytest.fixture(scope="module")
def engine():
    if settings_or_none() is None:
        pytest.skip("no database is configured, so there is no database to inspect")
    engine = _sync_engine()
    yield engine
    engine.dispose()


def test_metadata_and_database_hold_exactly_the_expected_tables(engine) -> None:
    """Both sides must agree, and neither may hold anything extra."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                "AND table_name <> 'alembic_version'"  # Alembic's own bookkeeping.
            )
        ).fetchall()

    assert {row[0] for row in rows} == EXPECTED_TABLES


def test_every_table_has_id_created_at_and_updated_at(engine) -> None:
    """Acceptance criterion 3, checked against the database, not the models."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND column_name IN ('id', 'created_at', 'updated_at')"
            )
        ).fetchall()

    found: dict[str, set[str]] = {}
    for table_name, column_name in rows:
        found.setdefault(table_name, set()).add(column_name)

    for table in EXPECTED_TABLES:
        assert found.get(table, set()) >= AUDIT_COLUMNS, f"{table} is missing an audit column"


def test_duplicate_source_natural_key_raises_integrity_error(engine) -> None:
    """Acceptance criterion 2: (source_system, source_id) may not repeat."""
    insert = text(
        "INSERT INTO contract "
        "(customer_ref, contract_number, status, currency, start_date, source_system, source_id) "
        "VALUES ('CUST-1', 'CON-1', 'active', 'USD', DATE '2026-01-01', :source_system, :source_id)"
    )
    params = {"source_system": "contract", "source_id": "duplicate-key-probe"}

    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(insert, params)
        with pytest.raises(IntegrityError):
            connection.execute(insert, params)
        # The failed statement leaves the transaction unusable; rolling back
        # also removes the first row, so the probe leaves nothing behind.
        transaction.rollback()


def test_money_columns_are_numeric_with_four_decimal_places(engine) -> None:
    """MoneyType must survive the migration, not degrade into a float column."""
    with engine.connect() as connection:
        row = connection.execute(
            text(
                "SELECT numeric_precision, numeric_scale FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = 'contract_term' "
                "AND column_name = 'value_numeric'"
            )
        ).one()

    assert row.numeric_precision == 20
    assert row.numeric_scale == 4


def test_embedding_column_matches_the_configured_width() -> None:
    """The column width is hard-coded in the model; it must not drift from Settings."""
    assert EMBEDDING_DIMENSIONS == get_settings().embedding_dimensions
    assert EMBEDDING_DIMENSIONS <= 2000, "pgvector cannot index wider vectors"


def test_money_round_trips_through_a_source_table(engine) -> None:
    """A real insert and read proves the column type, not just its declaration."""
    amount = Decimal("1234567.8910")

    with engine.connect() as connection, connection.begin() as transaction:
        connection.execute(
            text(
                "INSERT INTO credit_memo "
                "(customer_ref, credit_memo_number, amount, currency, source_system, source_id) "
                "VALUES ('CUST-1', 'CM-1', :amount, 'USD', 'billing', 'money-round-trip-probe')"
            ),
            {"amount": amount},
        )
        stored = connection.execute(
            text("SELECT amount FROM credit_memo WHERE source_id = 'money-round-trip-probe'")
        ).scalar_one()
        transaction.rollback()

    assert isinstance(stored, Decimal)
    assert stored == amount
    assert str(stored) == "1234567.8910"


def test_migration_up_down_up_succeeds() -> None:
    """Acceptance criterion 1: the revision has to be reversible, not just apply.

    This runs last, and leaves the database migrated, because it drops and then
    rebuilds every table.
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
