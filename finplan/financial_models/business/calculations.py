"""
Business Financial Model – calculation engine.

All figures entered are *typical monthly* amounts for an existing business.

Formulas
--------
Total revenue          = Sales + Other income + Custom income lines
Direct costs           = Cost of goods sold / direct service costs + custom "direct" lines
Gross profit           = Total revenue − Direct costs
Gross margin (%)       = Gross profit ÷ Total revenue × 100        (revenue > 0)
Operating expenses     = Salaries + Rent + Utilities + Marketing + Transport
                         + Software & admin + Other + custom "operating" lines
Operating profit       = Gross profit − Operating expenses
Profit before tax      = Operating profit  (this model has no interest or depreciation lines)
Estimated tax          = max(Profit before tax, 0) × Tax rate      (only when a rate is given)
Profit after tax       = Profit before tax − Estimated tax
Net margin (%)         = Profit after tax ÷ Total revenue × 100

Break-even (contribution margin method)
    Assumes direct costs rise and fall in proportion to revenue (variable)
    and operating expenses stay the same each month (fixed).
    Contribution margin ratio = (Revenue − Direct costs) ÷ Revenue
    Break-even revenue        = Operating expenses ÷ Contribution margin ratio
    Only calculated when the contribution margin ratio is positive.

12-month forecast
    Revenue in month m   = Revenue × (1 + revenue growth)^(m−1)
    Direct costs         = Revenue in month m × (Direct costs ÷ Revenue)
    Operating expenses   = Operating expenses × (1 + expense growth)^(m−1)
    Annual tax is estimated on the 12-month total profit before tax.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from ..common.finance import grow
from ..common.inputs import LineItem, a_date, dec, line_items, month_label, text
from ..common.money import ZERO, or_zero, pct_to_fraction, percentage, safe_divide
from ..common.scenarios import ScenarioAdjustment, scale

OPERATING_FIELDS = (
    ("salaries", "Salaries and wages"),
    ("rent", "Rent"),
    ("utilities", "Utilities"),
    ("marketing", "Marketing"),
    ("transport", "Transport and logistics"),
    ("software_admin", "Software and administration"),
    ("other_operating", "Other operating expenses"),
)


@dataclass(frozen=True)
class BusinessInputs:
    business_name: str
    forecast_start: date | None
    monthly_sales: Decimal
    direct_costs: Decimal
    other_income: Decimal | None = None
    operating: dict[str, Decimal | None] = field(default_factory=dict)
    custom_income: tuple[LineItem, ...] = ()
    custom_expenses: tuple[LineItem, ...] = ()
    tax_rate_pct: Decimal | None = None
    revenue_growth_pct: Decimal | None = None
    expense_growth_pct: Decimal | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessInputs":
        return cls(
            business_name=text(data, "business_name", text(data, "project_name")),
            forecast_start=a_date(data, "forecast_start"),
            monthly_sales=dec(data, "monthly_sales", required=True, label="Monthly sales revenue"),
            direct_costs=dec(data, "direct_costs", required=True, label="Cost of goods sold / direct costs"),
            other_income=dec(data, "other_income"),
            operating={key: dec(data, key) for key, _ in OPERATING_FIELDS},
            custom_income=tuple(line_items(data, "custom_income")),
            custom_expenses=tuple(line_items(data, "custom_expenses")),
            tax_rate_pct=dec(data, "tax_rate_pct"),
            revenue_growth_pct=dec(data, "revenue_growth_pct"),
            expense_growth_pct=dec(data, "expense_growth_pct"),
        )

    def adjusted(self, adj: ScenarioAdjustment) -> "BusinessInputs":
        """Apply a scenario: revenue %, cost %, and growth change in percentage points."""
        if adj.is_neutral:
            return self
        r, c = adj.revenue_pct, adj.cost_pct
        return replace(
            self,
            monthly_sales=scale(self.monthly_sales, r),
            other_income=scale(self.other_income, r),
            custom_income=tuple(replace(i, amount=scale(i.amount, r)) for i in self.custom_income),
            direct_costs=scale(self.direct_costs, c),
            operating={k: scale(v, c) for k, v in self.operating.items()},
            custom_expenses=tuple(replace(i, amount=scale(i.amount, c)) for i in self.custom_expenses),
            revenue_growth_pct=or_zero(self.revenue_growth_pct) + adj.extra,
        )


@dataclass(frozen=True)
class ForecastMonth:
    label: str
    revenue: Decimal
    direct_costs: Decimal
    gross_profit: Decimal
    operating_expenses: Decimal
    profit_before_tax: Decimal
    cumulative_profit: Decimal


@dataclass(frozen=True)
class BusinessResult:
    total_revenue: Decimal
    total_direct_costs: Decimal
    gross_profit: Decimal
    gross_margin_pct: Decimal | None
    total_operating_expenses: Decimal
    operating_profit: Decimal
    profit_before_tax: Decimal
    tax: Decimal | None
    profit_after_tax: Decimal
    net_margin_pct: Decimal | None
    contribution_margin_ratio: Decimal | None
    break_even_revenue: Decimal | None
    break_even_note: str
    margin_of_safety_pct: Decimal | None
    revenue_lines: list[tuple[str, Decimal]]
    expense_lines: list[tuple[str, Decimal, str]]  # (label, amount, "direct"/"operating")
    forecast: list[ForecastMonth]
    annual_revenue: Decimal
    annual_costs: Decimal
    annual_profit_before_tax: Decimal
    annual_tax: Decimal | None
    annual_profit_after_tax: Decimal


def calculate(inputs: BusinessInputs) -> BusinessResult:
    # --- Revenue -----------------------------------------------------------
    revenue_lines = [("Sales revenue", inputs.monthly_sales)]
    if inputs.other_income:
        revenue_lines.append(("Other business income", inputs.other_income))
    revenue_lines += [(item.name, item.amount) for item in inputs.custom_income]
    total_revenue = sum((amount for _, amount in revenue_lines), ZERO)

    # --- Costs ---------------------------------------------------------------
    expense_lines: list[tuple[str, Decimal, str]] = [("Cost of goods sold / direct costs", inputs.direct_costs, "direct")]
    for key, label in OPERATING_FIELDS:
        amount = inputs.operating.get(key)
        if amount:
            expense_lines.append((label, amount, "operating"))
    for item in inputs.custom_expenses:
        expense_lines.append((item.name, item.amount, "direct" if item.kind == "direct" else "operating"))

    total_direct = sum((a for _, a, k in expense_lines if k == "direct"), ZERO)
    total_operating = sum((a for _, a, k in expense_lines if k == "operating"), ZERO)

    # --- Profit --------------------------------------------------------------
    gross_profit = total_revenue - total_direct
    operating_profit = gross_profit - total_operating
    profit_before_tax = operating_profit
    tax_rate = None if inputs.tax_rate_pct is None else pct_to_fraction(inputs.tax_rate_pct)
    tax = None if tax_rate is None else max(profit_before_tax, ZERO) * tax_rate
    profit_after_tax = profit_before_tax - or_zero(tax)

    # --- Break-even ------------------------------------------------------------
    cm_ratio = safe_divide(gross_profit, total_revenue)
    if cm_ratio is None:
        break_even, note = None, "Enter revenue above zero to estimate break-even sales."
    elif cm_ratio <= 0:
        break_even, note = None, (
            "Direct costs are equal to or higher than revenue, so each extra sale does not "
            "contribute towards fixed costs. Break-even cannot be reached at current prices and costs."
        )
    else:
        break_even = total_operating / cm_ratio
        note = "Monthly revenue needed to cover all included costs, with no profit or loss."
    safety = None if break_even is None else percentage(total_revenue - break_even, total_revenue)

    # --- 12-month forecast ------------------------------------------------------
    revenue_growth = pct_to_fraction(inputs.revenue_growth_pct)
    expense_growth = pct_to_fraction(inputs.expense_growth_pct)
    direct_ratio = safe_divide(total_direct, total_revenue)
    forecast, cumulative = [], ZERO
    for month in range(1, 13):
        revenue = grow(total_revenue, revenue_growth, month - 1)
        # If there is no revenue we cannot express direct costs as a ratio; keep them flat.
        direct = revenue * direct_ratio if direct_ratio is not None else total_direct
        operating = grow(total_operating, expense_growth, month - 1)
        pbt = revenue - direct - operating
        cumulative += pbt
        forecast.append(ForecastMonth(
            label=month_label(inputs.forecast_start, month), revenue=revenue, direct_costs=direct,
            gross_profit=revenue - direct, operating_expenses=operating, profit_before_tax=pbt,
            cumulative_profit=cumulative,
        ))
    annual_revenue = sum((m.revenue for m in forecast), ZERO)
    annual_costs = sum((m.direct_costs + m.operating_expenses for m in forecast), ZERO)
    annual_pbt = annual_revenue - annual_costs
    annual_tax = None if tax_rate is None else max(annual_pbt, ZERO) * tax_rate

    return BusinessResult(
        total_revenue=total_revenue,
        total_direct_costs=total_direct,
        gross_profit=gross_profit,
        gross_margin_pct=percentage(gross_profit, total_revenue),
        total_operating_expenses=total_operating,
        operating_profit=operating_profit,
        profit_before_tax=profit_before_tax,
        tax=tax,
        profit_after_tax=profit_after_tax,
        net_margin_pct=percentage(profit_after_tax, total_revenue),
        contribution_margin_ratio=cm_ratio,
        break_even_revenue=break_even,
        break_even_note=note,
        margin_of_safety_pct=safety,
        revenue_lines=revenue_lines,
        expense_lines=expense_lines,
        forecast=forecast,
        annual_revenue=annual_revenue,
        annual_costs=annual_costs,
        annual_profit_before_tax=annual_pbt,
        annual_tax=annual_tax,
        annual_profit_after_tax=annual_pbt - or_zero(annual_tax),
    )
