"""Custom column types so money and periods are stored safely. See TICKET-004.

Plain-English: money is never a float, a currency is always three letters, and a
period is a half-open date range ``[start, end)`` -- never two loose dates that
someone can disagree about.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from psycopg.types.range import DateRange
from sqlalchemy import Numeric, String, types
from sqlalchemy.dialects.postgresql import DATERANGE
from sqlalchemy.engine import Dialect

# Money is stored with four decimal places: enough for currency minor units and
# for unit prices, and never a binary float.
MONEY_PRECISION = 20
MONEY_SCALE = 4
MONEY_QUANTUM = Decimal(1).scaleb(-MONEY_SCALE)  # 0.0001

CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


def quantize_money(value: Decimal) -> Decimal:
    """Round a Decimal to the stored scale the way AGENTS.md 1.4 requires."""
    return Decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


class MoneyType(types.TypeDecorator[Decimal]):
    """A money column: exact numeric, four decimal places, never a float.

    Values come back as ``Decimal`` already quantised, so callers can compare
    them without re-rounding.
    """

    impl = Numeric
    cache_ok = True

    def __init__(self) -> None:
        super().__init__(precision=MONEY_PRECISION, scale=MONEY_SCALE, asdecimal=True)

    def process_bind_param(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, float):
            raise TypeError(
                "money must be a Decimal or str, not a float: "
                "floats cannot represent currency exactly (AGENTS.md 1.4)"
            )
        return quantize_money(Decimal(value))

    def process_result_value(self, value: Any, dialect: Dialect) -> Decimal | None:
        if value is None:
            return None
        return quantize_money(Decimal(value))


class CurrencyCode(types.TypeDecorator[str]):
    """An ISO-4217 currency code, always upper case and exactly three letters."""

    impl = String(3)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        candidate = str(value).strip().upper()
        if not CURRENCY_CODE_PATTERN.match(candidate):
            raise ValueError(f"currency code must be three upper-case letters, got {value!r}")
        return candidate

    def process_result_value(self, value: Any, dialect: Dialect) -> str | None:
        if value is None:
            return None
        return str(value).strip().upper()


@dataclass(frozen=True, slots=True)
class HalfOpenInterval:
    """A period ``[start, end)``: start inclusive, end exclusive."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(f"end {self.end} must be after start {self.start}")

    def contains(self, moment: date) -> bool:
        return self.start <= moment < self.end

    def overlaps(self, other: HalfOpenInterval) -> bool:
        return self.start < other.end and other.start < self.end


class HalfOpenDateInterval(types.TypeDecorator[HalfOpenInterval]):
    """A half-open date range stored as a Postgres ``daterange`` with ``[)`` bounds.

    Half-open is the whole point: two adjacent periods share a boundary date and
    must never double-count it. See docs/billing-periods.md.
    """

    impl = DATERANGE
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> DateRange | None:
        if value is None:
            return None
        if not isinstance(value, HalfOpenInterval):
            raise TypeError(f"expected HalfOpenInterval, got {type(value).__name__}")
        return DateRange(value.start, value.end, bounds="[)")

    def process_result_value(self, value: Any, dialect: Dialect) -> HalfOpenInterval | None:
        if value is None:
            return None
        if isinstance(value, HalfOpenInterval):
            return value
        return HalfOpenInterval(start=value.lower, end=value.upper)
