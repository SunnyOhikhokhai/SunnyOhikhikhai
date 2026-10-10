"""
Helpers for reading saved project inputs.

Inputs are saved as JSON (numbers as strings, so no precision is lost).
These helpers turn them back into typed Python values and refuse to invent
a value for a *required* input that is missing.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .money import MissingInputError, to_decimal


def dec(data: dict, key: str, required: bool = False, label: str | None = None) -> Decimal | None:
    value = to_decimal(data.get(key))
    if value is None and required:
        raise MissingInputError(key, label)
    return value


def integer(data: dict, key: str, required: bool = False, label: str | None = None) -> int | None:
    value = to_decimal(data.get(key))
    if value is None:
        if required:
            raise MissingInputError(key, label)
        return None
    return int(value)


def text(data: dict, key: str, default: str = "") -> str:
    value = data.get(key)
    return default if value in (None, "") else str(value)


def a_date(data: dict, key: str) -> date | None:
    value = data.get(key)
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


@dataclass(frozen=True)
class LineItem:
    """A user-defined income or expense line, e.g. "Equipment hire: ₦50,000"."""

    name: str
    amount: Decimal
    kind: str = ""


def line_items(data: dict, key: str) -> list[LineItem]:
    items = []
    for raw in data.get(key) or []:
        amount = to_decimal(raw.get("amount"))
        if amount is None or not raw.get("name"):
            continue
        items.append(LineItem(name=str(raw["name"]), amount=amount, kind=str(raw.get("kind") or "")))
    return items


def serialise(value):
    """Convert cleaned form data into JSON-safe values (Decimal → str, date → ISO)."""
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: serialise(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialise(v) for v in value]
    return value


def month_label(start: date | None, index: int) -> str:
    """Label for forecast month ``index`` (1-based), e.g. "Mar 2027" or "Month 3"."""
    if start is None:
        return f"Month {index}"
    month0 = start.month - 1 + (index - 1)
    year = start.year + month0 // 12
    month = month0 % 12 + 1
    return date(year, month, 1).strftime("%b %Y")
