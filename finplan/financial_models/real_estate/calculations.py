"""
Real Estate Financial Model – calculation engine.

This is a feasibility estimate based on the costs the user includes. It is
not a property valuation.

Costs
-----
Acquisition cost         = Land cost + Legal and documentation
Development base         = Survey/design/planning + Construction/infrastructure
                           + Professional fees + Other costs
Contingency              = Development base × Contingency %
Total development cost   = Development base + Contingency + Marketing and sales
Total project cost       = Acquisition + Total development cost + Financing costs

Income
------
Sales revenue            = Units (plots) × Sale price per unit           (sales projects)
Gross rental income      = Annual rent × Rental years                    (rental projects)
Effective rental income  = Gross rental income × (1 − Vacancy %)
Rental operating costs   = Annual rental operating expenses × Rental years
Total revenue            = Sales revenue + Effective rental income

Profit and returns
------------------
Gross project profit     = Total revenue − (Total project cost − Financing costs)
Net project profit       = Total revenue − Total project cost − Rental operating costs
Profit margin (%)        = Net project profit ÷ Total revenue × 100
ROI (%)                  = Net project profit ÷ Total project cost × 100
                           (assumes the full project cost is the money invested)
Break-even price / unit  = (Total project cost + Rental operating costs − Effective rental income) ÷ Units
Gross rental yield (%)   = Annual rent ÷ Total project cost × 100
Net rental yield (%)     = (Annual rent × (1 − Vacancy %) − Annual operating costs) ÷ Total project cost × 100

Land subdivision
----------------
Net saleable area        = Gross land area × (1 − (Roads + Drainage + Public space + Other %) ÷ 100)
Maximum plots            = Net saleable area ÷ Plot size (rounded down)

Cash-flow timeline (monthly, simplified)
---------------------------------------
* Month 1: acquisition costs.
* Survey/design: spread evenly over the first three months (or the project length if shorter).
* Construction, professional fees, other costs, contingency and financing: spread evenly across the project.
* Sales income and marketing costs: spread evenly from the sales start month to the end of the project.
* Rental income (net of vacancy and operating costs): monthly after completion for the rental period.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import ROUND_FLOOR, Decimal

from ..common.inputs import LineItem, dec, integer, line_items, text
from ..common.money import HUNDRED, ONE, ZERO, or_zero, pct_to_fraction, percentage, safe_divide
from ..common.scenarios import ScenarioAdjustment, scale

PROJECT_TYPES = [
    ("residential", "Residential development"),
    ("commercial", "Commercial development"),
    ("mixed_use", "Mixed-use development"),
    ("land_subdivision", "Land subdivision (plots)"),
    ("rental", "Rental property"),
]
INCOME_TYPES = [("sales", "Sales only"), ("rental", "Rental only"), ("both", "Sales and rental")]

DEV_FIELDS = (
    ("survey_design", "Survey, design and planning"),
    ("construction", "Construction or infrastructure"),
    ("professional_fees", "Professional fees"),
)
SUBDIVISION_FIELDS = ("roads_pct", "drainage_pct", "public_space_pct", "other_unsaleable_pct")


@dataclass(frozen=True)
class RealEstateInputs:
    location: str
    project_type: str
    income_type: str
    land_cost: Decimal
    legal_docs: Decimal | None
    survey_design: Decimal | None
    construction: Decimal
    professional_fees: Decimal | None
    marketing_sales: Decimal | None
    contingency_pct: Decimal | None
    financing_costs: Decimal | None
    other_costs: tuple[LineItem, ...]
    duration_months: int
    units: int | None = None
    sale_price_per_unit: Decimal | None = None
    sales_start_month: int | None = None
    annual_rent: Decimal | None = None
    vacancy_pct: Decimal | None = None
    annual_rental_expenses: Decimal | None = None
    rental_years: int | None = None
    gross_land_area: Decimal | None = None
    roads_pct: Decimal | None = None
    drainage_pct: Decimal | None = None
    public_space_pct: Decimal | None = None
    other_unsaleable_pct: Decimal | None = None
    plot_size: Decimal | None = None

    @property
    def has_sales(self) -> bool:
        return self.income_type in ("sales", "both")

    @property
    def has_rental(self) -> bool:
        return self.income_type in ("rental", "both")

    @classmethod
    def from_dict(cls, data: dict) -> "RealEstateInputs":
        income_type = text(data, "income_type", "sales")
        sales = income_type in ("sales", "both")
        rental = income_type in ("rental", "both")
        return cls(
            location=text(data, "location"),
            project_type=text(data, "project_type", "residential"),
            income_type=income_type,
            land_cost=dec(data, "land_cost", required=True, label="Land acquisition cost"),
            legal_docs=dec(data, "legal_docs"),
            survey_design=dec(data, "survey_design"),
            construction=dec(data, "construction", required=True, label="Construction or infrastructure cost"),
            professional_fees=dec(data, "professional_fees"),
            marketing_sales=dec(data, "marketing_sales"),
            contingency_pct=dec(data, "contingency_pct"),
            financing_costs=dec(data, "financing_costs"),
            other_costs=tuple(line_items(data, "other_costs")),
            duration_months=integer(data, "duration_months", required=True, label="Project duration"),
            units=integer(data, "units", required=sales, label="Number of plots or units"),
            sale_price_per_unit=dec(data, "sale_price_per_unit", required=sales, label="Sale price per unit"),
            sales_start_month=integer(data, "sales_start_month"),
            annual_rent=dec(data, "annual_rent", required=rental, label="Annual rental income"),
            vacancy_pct=dec(data, "vacancy_pct"),
            annual_rental_expenses=dec(data, "annual_rental_expenses"),
            rental_years=integer(data, "rental_years", required=rental, label="Rental period"),
            gross_land_area=dec(data, "gross_land_area"),
            roads_pct=dec(data, "roads_pct"),
            drainage_pct=dec(data, "drainage_pct"),
            public_space_pct=dec(data, "public_space_pct"),
            other_unsaleable_pct=dec(data, "other_unsaleable_pct"),
            plot_size=dec(data, "plot_size"),
        )

    def adjusted(self, adj: ScenarioAdjustment) -> "RealEstateInputs":
        """Revenue % changes prices and rent; cost % changes development and running costs
        (not the land price); extra adds months to the project duration."""
        if adj.is_neutral:
            return self
        r, c = adj.revenue_pct, adj.cost_pct
        delta = int(adj.extra)
        duration = max(1, self.duration_months + delta)
        start = self.sales_start_month
        if start is not None:
            start = min(max(1, start + delta), duration)
        return replace(
            self,
            sale_price_per_unit=scale(self.sale_price_per_unit, r),
            annual_rent=scale(self.annual_rent, r),
            survey_design=scale(self.survey_design, c),
            construction=scale(self.construction, c),
            professional_fees=scale(self.professional_fees, c),
            marketing_sales=scale(self.marketing_sales, c),
            other_costs=tuple(replace(i, amount=scale(i.amount, c)) for i in self.other_costs),
            annual_rental_expenses=scale(self.annual_rental_expenses, c),
            duration_months=duration,
            sales_start_month=start,
        )


@dataclass(frozen=True)
class Subdivision:
    gross_area: Decimal
    unsaleable_pct: Decimal
    net_saleable_area: Decimal
    max_plots: int | None


@dataclass(frozen=True)
class TimelinePeriod:
    label: str
    costs: Decimal
    income: Decimal
    net: Decimal
    cumulative: Decimal


@dataclass(frozen=True)
class RealEstateResult:
    acquisition_cost: Decimal
    development_base: Decimal
    contingency: Decimal
    marketing: Decimal
    financing: Decimal
    total_development_cost: Decimal
    total_project_cost: Decimal
    cost_lines: list[tuple[str, Decimal]]
    sales_revenue: Decimal
    gross_rental_income: Decimal
    vacancy_loss: Decimal
    effective_rental_income: Decimal
    rental_operating_costs: Decimal
    total_revenue: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin_pct: Decimal | None
    roi_pct: Decimal | None
    break_even_price: Decimal | None
    gross_yield_pct: Decimal | None
    net_yield_pct: Decimal | None
    subdivision: Subdivision | None
    timeline: list[TimelinePeriod]
    peak_cash_need: Decimal
    sales_start_month: int | None


def _spread(total: Decimal, months: list[int], timeline: dict[int, Decimal]) -> None:
    if not months or total == 0:
        return
    share = total / len(months)
    for month in months:
        timeline[month] = timeline.get(month, ZERO) + share


def calculate(inputs: RealEstateInputs) -> RealEstateResult:
    duration = inputs.duration_months

    # --- Costs -----------------------------------------------------------------
    acquisition = inputs.land_cost + or_zero(inputs.legal_docs)
    other_total = sum((item.amount for item in inputs.other_costs), ZERO)
    development_base = (or_zero(inputs.survey_design) + inputs.construction
                        + or_zero(inputs.professional_fees) + other_total)
    contingency = development_base * pct_to_fraction(inputs.contingency_pct)
    marketing = or_zero(inputs.marketing_sales)
    financing = or_zero(inputs.financing_costs)
    total_development = development_base + contingency + marketing
    total_cost = acquisition + total_development + financing

    cost_lines = [("Land acquisition", inputs.land_cost)]
    if inputs.legal_docs:
        cost_lines.append(("Legal and documentation", inputs.legal_docs))
    for key, label in DEV_FIELDS:
        value = getattr(inputs, key)
        if value:
            cost_lines.append((label, value))
    cost_lines += [(item.name, item.amount) for item in inputs.other_costs]
    if contingency:
        cost_lines.append(("Contingency allowance", contingency))
    if marketing:
        cost_lines.append(("Marketing and sales", marketing))
    if financing:
        cost_lines.append(("Financing costs", financing))

    # --- Income ----------------------------------------------------------------
    sales_revenue = ZERO
    if inputs.has_sales:
        sales_revenue = Decimal(inputs.units) * inputs.sale_price_per_unit
    gross_rent = vacancy_loss = effective_rent = rental_costs = ZERO
    years = inputs.rental_years or 0
    vacancy = pct_to_fraction(inputs.vacancy_pct)
    if inputs.has_rental:
        gross_rent = inputs.annual_rent * years
        vacancy_loss = gross_rent * vacancy
        effective_rent = gross_rent - vacancy_loss
        rental_costs = or_zero(inputs.annual_rental_expenses) * years
    total_revenue = sales_revenue + effective_rent

    # --- Profit ----------------------------------------------------------------
    gross_profit = total_revenue - (total_cost - financing)
    net_profit = total_revenue - total_cost - rental_costs

    break_even_price = None
    if inputs.has_sales and inputs.units:
        break_even_price = (total_cost + rental_costs - effective_rent) / Decimal(inputs.units)

    gross_yield = net_yield = None
    if inputs.has_rental:
        gross_yield = percentage(inputs.annual_rent, total_cost)
        annual_net = inputs.annual_rent * (ONE - vacancy) - or_zero(inputs.annual_rental_expenses)
        net_yield = percentage(annual_net, total_cost)

    # --- Land subdivision --------------------------------------------------------
    subdivision = None
    if inputs.project_type == "land_subdivision" and inputs.gross_land_area:
        unsaleable = sum((or_zero(getattr(inputs, f)) for f in SUBDIVISION_FIELDS), ZERO)
        net_area = inputs.gross_land_area * (ONE - unsaleable / HUNDRED)
        max_plots = None
        if inputs.plot_size:
            plots = safe_divide(net_area, inputs.plot_size)
            max_plots = int(plots.to_integral_value(rounding=ROUND_FLOOR)) if plots is not None else None
        subdivision = Subdivision(inputs.gross_land_area, unsaleable, net_area, max_plots)

    # --- Timeline ----------------------------------------------------------------
    project_months = list(range(1, duration + 1))
    sales_start = None
    costs: dict[int, Decimal] = {1: acquisition}
    income: dict[int, Decimal] = {}
    _spread(or_zero(inputs.survey_design), project_months[:3], costs)
    _spread(inputs.construction + or_zero(inputs.professional_fees) + other_total + contingency + financing,
            project_months, costs)
    if inputs.has_sales:
        sales_start = inputs.sales_start_month or (duration // 2 + 1 if duration > 1 else 1)
        sales_start = min(max(1, sales_start), duration)
        sales_months = list(range(sales_start, duration + 1))
        _spread(sales_revenue, sales_months, income)
        _spread(marketing, sales_months, costs)
    else:
        _spread(marketing, project_months, costs)
    if inputs.has_rental and years:
        rental_months = list(range(duration + 1, duration + 12 * years + 1))
        _spread(effective_rent, rental_months, income)
        _spread(rental_costs, rental_months, costs)

    last_month = max([duration, *costs.keys(), *income.keys()])
    timeline, cumulative, lowest = [], ZERO, ZERO
    for month in range(1, last_month + 1):
        cost = costs.get(month, ZERO)
        inc = income.get(month, ZERO)
        cumulative += inc - cost
        lowest = min(lowest, cumulative)
        timeline.append(TimelinePeriod(f"Month {month}", cost, inc, inc - cost, cumulative))

    return RealEstateResult(
        acquisition_cost=acquisition,
        development_base=development_base,
        contingency=contingency,
        marketing=marketing,
        financing=financing,
        total_development_cost=total_development,
        total_project_cost=total_cost,
        cost_lines=cost_lines,
        sales_revenue=sales_revenue,
        gross_rental_income=gross_rent,
        vacancy_loss=vacancy_loss,
        effective_rental_income=effective_rent,
        rental_operating_costs=rental_costs,
        total_revenue=total_revenue,
        gross_profit=gross_profit,
        net_profit=net_profit,
        profit_margin_pct=percentage(net_profit, total_revenue),
        roi_pct=percentage(net_profit, total_cost),
        break_even_price=break_even_price,
        gross_yield_pct=gross_yield,
        net_yield_pct=net_yield,
        subdivision=subdivision,
        timeline=timeline,
        peak_cash_need=-lowest,
        sales_start_month=sales_start,
    )
