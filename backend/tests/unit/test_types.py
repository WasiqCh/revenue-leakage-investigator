"""Column type behaviour that needs no database. See TICKET-004."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.db.types import (
    CurrencyCode,
    HalfOpenDateInterval,
    HalfOpenInterval,
    MoneyType,
    quantize_money,
)


def test_money_quantizes_to_four_decimal_places() -> None:
    assert quantize_money(Decimal("1.23456")) == Decimal("1.2346")
    assert quantize_money(Decimal("1.23444")) == Decimal("1.2344")
    assert quantize_money(Decimal("19.99")) == Decimal("19.9900")


def test_money_type_rejects_floats() -> None:
    column = MoneyType()

    with pytest.raises(TypeError, match="not a float"):
        column.process_bind_param(19.99, None)  # type: ignore[arg-type]


def test_money_type_passes_none_through() -> None:
    column = MoneyType()

    assert column.process_bind_param(None, None) is None
    assert column.process_result_value(None, None) is None


def test_currency_code_is_normalised_and_validated() -> None:
    column = CurrencyCode()

    assert column.process_bind_param("usd", None) == "USD"

    with pytest.raises(ValueError, match="three upper-case letters"):
        column.process_bind_param("dollars", None)


def test_half_open_interval_is_start_inclusive_end_exclusive() -> None:
    period = HalfOpenInterval(start=date(2026, 1, 1), end=date(2026, 2, 1))

    assert period.contains(date(2026, 1, 1))
    assert period.contains(date(2026, 1, 31))
    assert not period.contains(date(2026, 2, 1))


def test_adjacent_intervals_do_not_overlap() -> None:
    first = HalfOpenInterval(start=date(2026, 1, 1), end=date(2026, 2, 1))
    second = HalfOpenInterval(start=date(2026, 2, 1), end=date(2026, 3, 1))

    assert not first.overlaps(second)
    assert first.overlaps(HalfOpenInterval(start=date(2026, 1, 15), end=date(2026, 3, 1)))


def test_interval_rejects_an_end_that_is_not_after_the_start() -> None:
    with pytest.raises(ValueError, match="must be after start"):
        HalfOpenInterval(start=date(2026, 2, 1), end=date(2026, 2, 1))


def test_interval_round_trips_through_the_column_type() -> None:
    column = HalfOpenDateInterval()
    period = HalfOpenInterval(start=date(2026, 1, 1), end=date(2026, 2, 1))

    stored = column.process_bind_param(period, None)
    assert stored is not None
    assert stored.bounds == "[)"

    restored = column.process_result_value(stored, None)
    assert restored == period
