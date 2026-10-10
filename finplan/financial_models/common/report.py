"""
Presentation structures.

Each model turns its calculation result into a ``Report``. The same Report
feeds the on-screen results page, the printable page and the PDF, so the
three always show identical figures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .money import format_compact, format_money, format_number, format_percent


def tone(value: Decimal | None) -> str:
    """Visual tone for a figure: positive, negative or neutral."""
    if value is None or value == 0:
        return "neutral"
    return "positive" if value > 0 else "negative"


@dataclass
class Formatter:
    """Formats values in the project's currency for one output style."""

    currency: str
    style: str = "symbol"  # "symbol" for screens, "code" for PDFs

    def money(self, value: Decimal | None) -> str:
        return format_money(value, self.currency, self.style)

    def compact(self, value: Decimal | None) -> str:
        return format_compact(value, self.currency, self.style)

    @staticmethod
    def pct(value: Decimal | None, decimals: int = 1) -> str:
        return format_percent(value, decimals)

    @staticmethod
    def number(value: Decimal | None, decimals: int = 0) -> str:
        return format_number(value, decimals)


@dataclass
class Metric:
    label: str
    value: str
    tone: str = "neutral"
    help: str = ""


@dataclass
class Table:
    title: str
    columns: list[str]
    rows: list[list[str]]
    note: str = ""
    # Optional per-row tones (e.g. highlight a negative cash balance).
    row_tones: list[str] = field(default_factory=list)
    total_row: bool = False

    @property
    def styled_rows(self) -> list[tuple[list[str], str]]:
        """Rows paired with their tone, for templates."""
        tones = self.row_tones + ["neutral"] * (len(self.rows) - len(self.row_tones))
        return list(zip(self.rows, tones))


@dataclass
class Series:
    name: str
    values: list[Decimal]
    colour: str  # one of: blue, green, red, navy, slate


@dataclass
class Chart:
    title: str
    kind: str  # "bar" or "line"
    labels: list[str]
    series: list[Series]
    description: str = ""


@dataclass
class Section:
    title: str
    metrics: list[Metric]
    intro: str = ""


@dataclass
class Report:
    model_label: str
    headline: list[Metric]
    sections: list[Section] = field(default_factory=list)
    charts: list[Chart] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    scenario_table: Table | None = None
    assumptions: list[tuple[str, str]] = field(default_factory=list)
    explanations: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def aggregate_periods(labels: list[str], rows: list[list[Decimal]], size: int, prefix: str) -> tuple[list[str], list[list[Decimal]]]:
    """
    Sum consecutive periods (e.g. months into quarters) for long timelines.

    ``rows`` is a list of columns' values per period. Columns flagged as
    balances should be aggregated by the caller using the last value instead.
    """
    if size <= 1:
        return labels, rows
    new_labels, new_rows = [], []
    for start in range(0, len(rows), size):
        chunk = rows[start:start + size]
        new_labels.append(f"{prefix} {start // size + 1}")
        new_rows.append([sum((r[i] for r in chunk), Decimal("0")) for i in range(len(chunk[0]))])
    return new_labels, new_rows


SCENARIO_NOTE = (
    "Scenarios are projections based on the adjustments you chose. They are not "
    "predictions or guarantees of what will happen."
)


def scenario_table(names: dict[str, str], results: dict, rows: list[tuple[str, callable]],
                   adjustments: dict | None = None, lever_label: str = "") -> Table:
    """Build a comparison table: one row per metric, one column per scenario."""
    order = ("conservative", "expected", "optimistic")
    columns = ["Measure"] + [names[key] for key in order]
    body = []
    if adjustments:
        body.append(["Income / price change"] + [format_percent(adjustments[k].revenue_pct) for k in order])
        body.append(["Cost change"] + [format_percent(adjustments[k].cost_pct) for k in order])
        if lever_label:
            body.append([lever_label] + [format_number(adjustments[k].extra, 1) for k in order])
    for label, getter in rows:
        body.append([label] + [getter(results[key]) for key in order])
    return Table(title="Scenario comparison", columns=columns, rows=body, note=SCENARIO_NOTE)


__all__ = [
    "Chart", "Formatter", "Metric", "Report", "Section", "Series", "Table",
    "aggregate_periods", "tone",
]
