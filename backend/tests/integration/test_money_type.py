"""Money must survive a real round trip. See TICKET-004.

Acceptance criterion: a test round-trips a Decimal money column with four
decimal places and no float drift. This runs against the Postgres service from
docker-compose; it skips when no database is reachable.
"""

from __future__ import annotations

import os
from decimal import Decimal

import psycopg
import pytest

DRIVER_PREFIX = "postgresql+psycopg://"


def _dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not set, so there is no database to test against")
    return dsn.replace(DRIVER_PREFIX, "postgresql://")


@pytest.fixture
def connection() -> psycopg.Connection[tuple]:  # type: ignore[type-arg]
    with psycopg.connect(_dsn()) as raw:
        yield raw


def test_money_round_trips_without_float_drift(connection: psycopg.Connection[tuple]) -> None:  # type: ignore[type-arg]
    amount = Decimal("1234567.8910")

    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS tmp_money_round_trip")
        cursor.execute("CREATE TABLE tmp_money_round_trip (amount numeric(20, 4))")
        cursor.execute("INSERT INTO tmp_money_round_trip (amount) VALUES (%s)", (amount,))
        cursor.execute("SELECT amount FROM tmp_money_round_trip")
        row = cursor.fetchone()
        assert row is not None
        stored = row[0]
        cursor.execute("DROP TABLE tmp_money_round_trip")

    assert isinstance(stored, Decimal), f"expected Decimal, got {type(stored).__name__}"
    assert not isinstance(stored, float)
    assert stored == amount
    # Four decimal places preserved, and no binary-float noise in the digits.
    assert -stored.as_tuple().exponent == 4
    assert str(stored) == "1234567.8910"


def test_money_is_exact_under_addition(connection: psycopg.Connection[tuple]) -> None:  # type: ignore[type-arg]
    """0.1 + 0.2 must be 0.3 exactly, which floats cannot guarantee."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT %s::numeric(20, 4) + %s::numeric(20, 4)", (Decimal("0.10"), Decimal("0.20"))
        )
        row = cursor.fetchone()
        assert row is not None
        total = row[0]

    assert total == Decimal("0.30")
