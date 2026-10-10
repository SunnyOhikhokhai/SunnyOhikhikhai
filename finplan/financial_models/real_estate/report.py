"""Turns a Real Estate model result into a presentable Report."""
from decimal import Decimal

from ..common.money import format_number, format_percent
from ..common.report import Chart, Formatter, Metric, Report, Section, Series, Table, scenario_table, tone
from ..common.scenarios import read_adjustments
from .calculations import INCOME_TYPES, PROJECT_TYPES, RealEstateInputs, calculate

SCENARIO_NAMES = {"conservative": "Conservative", "expected": "Expected", "optimistic": "Optimistic"}


def _grouped_timeline(timeline):
    """Group long timelines into quarters or years so tables and charts stay readable."""
    size, name = 1, "Month"
    if len(timeline) > 96:
        size, name = 12, "Year"
    elif len(timeline) > 36:
        size, name = 3, "Quarter"
    if size == 1:
        return [(p.label, p.costs, p.income, p.net, p.cumulative) for p in timeline], name
    grouped = []
    for start in range(0, len(timeline), size):
        chunk = timeline[start:start + size]
        grouped.append((f"{name} {start // size + 1}", sum((p.costs for p in chunk), Decimal(0)),
                        sum((p.income for p in chunk), Decimal(0)), sum((p.net for p in chunk), Decimal(0)),
                        chunk[-1].cumulative))
    return grouped, name


def build_report(data: dict, fmt: Formatter) -> Report:
    inputs = RealEstateInputs.from_dict(data)
    result = calculate(inputs)
    m = fmt.money

    headline = [
        Metric("Total project cost", m(result.total_project_cost), "neutral", "All acquisition, development and financing costs included."),
        Metric("Projected revenue", m(result.total_revenue), "neutral", "Sales income plus rental income after vacancies."),
        Metric("Net project profit", m(result.net_profit), tone(result.net_profit),
               "Revenue minus all included costs. Based only on the costs you entered."),
        Metric("Return on investment (ROI)", format_percent(result.roi_pct), tone(result.roi_pct),
               "Net profit as a share of total project cost, over the whole project – not per year."),
    ]

    cost_section = Section("Costs", [
        Metric("Total acquisition cost", m(result.acquisition_cost), help="Land plus legal and documentation."),
        Metric("Total development cost", m(result.total_development_cost),
               help="Design, construction, professional fees, other costs, contingency and marketing."),
        Metric("Contingency allowance", m(result.contingency)),
        Metric("Financing costs", m(result.financing)),
        Metric("Total project cost", m(result.total_project_cost)),
        Metric("Peak cash requirement", m(result.peak_cash_need),
               help="The most cash tied up at any point in the timeline, before income catches up with spending."),
    ])
    income_metrics = []
    if inputs.has_sales:
        income_metrics += [
            Metric("Projected sales revenue", m(result.sales_revenue)),
            Metric("Break-even price per unit", m(result.break_even_price) if result.break_even_price is not None else "Not available",
                   tone(None if result.break_even_price is None else inputs.sale_price_per_unit - result.break_even_price),
                   "The lowest average price per plot or unit that covers all included costs."),
        ]
    if inputs.has_rental:
        income_metrics += [
            Metric("Projected rental revenue", m(result.effective_rental_income),
                   help=f"{inputs.rental_years} year(s) of rent after a {format_percent(inputs.vacancy_pct or Decimal(0))} vacancy allowance."),
            Metric("Gross rental yield", format_percent(result.gross_yield_pct), help="Annual rent ÷ total project cost."),
            Metric("Net rental yield", format_percent(result.net_yield_pct), tone(result.net_yield_pct),
                   "Annual rent after vacancies and operating expenses ÷ total project cost."),
        ]
    income_metrics += [
        Metric("Gross project profit", m(result.gross_profit), tone(result.gross_profit), "Revenue minus all costs except financing."),
        Metric("Net project profit", m(result.net_profit), tone(result.net_profit)),
        Metric("Profit margin", format_percent(result.profit_margin_pct), tone(result.profit_margin_pct),
               "Net profit as a share of revenue."),
    ]
    sections = [cost_section, Section("Income and profit", income_metrics)]
    if result.subdivision:
        sub = result.subdivision
        sections.append(Section("Land subdivision", [
            Metric("Gross land area", f"{format_number(sub.gross_area)} m²"),
            Metric("Land set aside (not saleable)", format_percent(sub.unsaleable_pct)),
            Metric("Net saleable area", f"{format_number(sub.net_saleable_area)} m²"),
            Metric("Maximum plots at this plot size", format_number(Decimal(sub.max_plots)) if sub.max_plots is not None else "Enter a plot size"),
        ], intro="Roads, drainage and public spaces reduce the land you can sell."))

    grouped, period_name = _grouped_timeline(result.timeline)
    labels = [row[0] for row in grouped]
    charts = [
        Chart("Project costs versus income", "bar", ["Costs", "Revenue"], [
            Series("Amount", [result.total_project_cost + result.rental_operating_costs, result.total_revenue], "blue"),
        ], "Total costs (including rental operating costs) compared with total projected revenue."),
        Chart(f"Cumulative project cash flow (by {period_name.lower()})", "line", labels, [
            Series("Cumulative cash", [row[4] for row in grouped], "navy"),
        ], "Below zero means money is still tied up in the project. The lowest point is the peak cash requirement."),
    ]

    tables = [
        Table("Cost breakdown", ["Cost", "Amount", "Share of total"],
              [[label, m(amount), format_percent(None if result.total_project_cost == 0 else amount / result.total_project_cost * 100)]
               for label, amount in result.cost_lines]
              + [["Total project cost", m(result.total_project_cost), "100.0%" if result.total_project_cost else "Not available"]],
              total_row=True),
        Table(f"Project cash-flow timeline (by {period_name.lower()})", [period_name, "Costs", "Income", "Net cash flow", "Cumulative"],
              [[row[0], m(row[1]), m(row[2]), m(row[3]), m(row[4])] for row in grouped],
              note="Simplified timing: costs and income are spread evenly as described in the assumptions.",
              row_tones=["negative" if row[4] < 0 else "neutral" for row in grouped]),
    ]

    adjustments = read_adjustments(data)
    scenario_results = {key: calculate(inputs.adjusted(adj)) for key, adj in adjustments.items()}
    scenarios = scenario_table(SCENARIO_NAMES, scenario_results, [
        ("Total revenue", lambda r: m(r.total_revenue)),
        ("Total project cost", lambda r: m(r.total_project_cost)),
        ("Net project profit", lambda r: m(r.net_profit)),
        ("Profit margin", lambda r: format_percent(r.profit_margin_pct)),
        ("ROI", lambda r: format_percent(r.roi_pct)),
        ("Peak cash requirement", lambda r: m(r.peak_cash_need)),
    ], adjustments, "Delay (months)")

    labels_type = dict(PROJECT_TYPES)
    labels_income = dict(INCOME_TYPES)
    assumptions = [
        ("Project type", labels_type.get(inputs.project_type, inputs.project_type)),
        ("Location", inputs.location or "Not provided"),
        ("Income type", labels_income.get(inputs.income_type, inputs.income_type)),
        ("Project duration", f"{inputs.duration_months} months"),
        ("Contingency", format_percent(inputs.contingency_pct, 2) + " of design, construction, professional and other costs"
         if inputs.contingency_pct else "None included"),
    ]
    if inputs.has_sales:
        assumptions += [
            ("Plots or units for sale", format_number(Decimal(inputs.units))),
            ("Sale price per unit", m(inputs.sale_price_per_unit)),
            ("Sales period", f"Month {result.sales_start_month} to month {inputs.duration_months}, spread evenly"),
        ]
    if inputs.has_rental:
        assumptions += [
            ("Annual rent (fully let)", m(inputs.annual_rent)),
            ("Vacancy allowance", format_percent(inputs.vacancy_pct or Decimal(0), 2)),
            ("Annual rental operating expenses", m(inputs.annual_rental_expenses) if inputs.annual_rental_expenses else "Not included"),
            ("Rental period", f"{inputs.rental_years} year(s) after completion"),
        ]
    assumptions.append(("ROI basis", "Net profit ÷ total project cost (assumes the whole cost is invested)"))

    warnings = []
    if result.subdivision and result.subdivision.max_plots is not None and inputs.has_sales and inputs.units > result.subdivision.max_plots:
        warnings.append(f"You plan to sell {inputs.units} plots, but the net saleable area only fits about "
                        f"{result.subdivision.max_plots} plots of {format_number(inputs.plot_size)} m².")
    if inputs.project_type == "land_subdivision" and not result.subdivision:
        warnings.append("Add the gross land area to check how much land is actually saleable.")
    if result.net_profit < 0:
        warnings.append("At these figures the project makes a loss.")
    if not inputs.contingency_pct:
        warnings.append("No contingency allowance is included. Property projects often cost more than planned.")

    return Report(
        model_label="Real Estate Financial Model",
        headline=headline,
        sections=sections,
        charts=charts,
        tables=tables,
        scenario_table=scenarios,
        assumptions=assumptions,
        explanations=[
            ("Not a valuation", "This is a feasibility estimate based on the costs and prices you entered. It is not a "
             "professional property valuation and does not replace one."),
            ("ROI versus yearly return", "ROI here covers the whole project period. A 30% ROI over three years is not the same as 30% a year."),
        ],
        warnings=warnings,
        limitations=[
            "Costs and income are spread evenly over time; real projects are lumpier.",
            "Taxes, inflation and price changes during the project are not included.",
            "Only the costs you entered are included. Anything left out will make profit look higher.",
        ],
    )
