"""
Scenario analysis shared by all four models.

A scenario is the user's base ("expected") inputs with three simple
adjustments applied:

* ``revenue_pct``  – change income/prices by this percentage
* ``cost_pct``     – change costs by this percentage
* ``extra``        – one model-specific lever (growth, duration or exit value)

Scenarios are projections from assumptions, not predictions.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .money import HUNDRED, ONE, to_decimal

SCENARIO_KEYS = ("conservative", "expected", "optimistic")


@dataclass(frozen=True)
class ScenarioAdjustment:
    revenue_pct: Decimal = Decimal("0")
    cost_pct: Decimal = Decimal("0")
    extra: Decimal = Decimal("0")

    @property
    def is_neutral(self) -> bool:
        return self.revenue_pct == 0 and self.cost_pct == 0 and self.extra == 0


@dataclass(frozen=True)
class ExtraLever:
    """Describes the model-specific scenario lever for forms and reports."""

    label: str
    help: str
    unit: str  # "points", "months" or "%"
    conservative: Decimal
    optimistic: Decimal
    min_value: Decimal
    max_value: Decimal


DEFAULT_REVENUE = {"conservative": Decimal("-15"), "optimistic": Decimal("10")}
DEFAULT_COST = {"conservative": Decimal("10"), "optimistic": Decimal("-5")}


def scale(value: Decimal | None, pct: Decimal) -> Decimal | None:
    """Increase/decrease ``value`` by ``pct`` per cent. Blank stays blank."""
    if value is None:
        return None
    return value * (ONE + pct / HUNDRED)


def field_name(scenario: str, lever: str) -> str:
    return f"scn_{scenario}_{lever}"


def read_adjustments(data: dict) -> dict[str, ScenarioAdjustment]:
    """Read scenario settings from saved inputs; ``expected`` is always neutral."""
    result = {"expected": ScenarioAdjustment()}
    for key in ("conservative", "optimistic"):
        values = {}
        for lever in ("revenue_pct", "cost_pct", "extra"):
            values[lever] = to_decimal(data.get(field_name(key, lever))) or Decimal("0")
        result[key] = ScenarioAdjustment(**values)
    return result
