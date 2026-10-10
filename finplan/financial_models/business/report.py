"""Turns a Business model result into a presentable Report."""
from ..common.money import format_percent
from ..common.report import Chart, Formatter, Metric, Report, Section, Series, Table, scenario_table, tone
from ..common.scenarios import read_adjustments
from .calculations import BusinessInputs, calculate

SCENARIO_NAMES = {"conservative": "Conservative", "expected": "Expected", "optimistic": "Optimistic"}

PROFIT_HELP = "Net profit is the amount left after the expenses included in this model have been deducted from revenue."


def build_report(data: dict, fmt: Formatter) -> Report:
    inputs = BusinessInputs.from_dict(data)
    result = calculate(inputs)
    m = fmt.money

    has_tax = result.tax is not None
    net_label = "Estimated monthly profit after tax" if has_tax else "Estimated monthly profit (before tax)"

    headline = [
        Metric("Monthly revenue", m(result.total_revenue), "neutral", "All income included in this model for a typical month."),
        Metric(net_label, m(result.profit_after_tax), tone(result.profit_after_tax), PROFIT_HELP),
        Metric("Net profit margin", format_percent(result.net_margin_pct), tone(result.net_margin_pct),
               "How many of every 100 units of revenue are left as profit."),
        Metric("Break-even monthly sales", m(result.break_even_revenue) if result.break_even_revenue is not None else "Not reachable",
               "neutral" if result.break_even_revenue is not None else "negative", result.break_even_note),
    ]

    profit_section = Section("Monthly profit and loss", [
        Metric("Total revenue", m(result.total_revenue)),
        Metric("Direct costs", m(result.total_direct_costs), help="Costs that rise and fall with sales."),
        Metric("Gross profit", m(result.gross_profit), tone(result.gross_profit), "Revenue minus direct costs."),
        Metric("Gross profit margin", format_percent(result.gross_margin_pct), tone(result.gross_margin_pct)),
        Metric("Operating expenses", m(result.total_operating_expenses), help="Running costs such as salaries, rent and utilities."),
        Metric("Operating profit", m(result.operating_profit), tone(result.operating_profit), "Gross profit minus operating expenses."),
        Metric("Estimated profit before tax", m(result.profit_before_tax), tone(result.profit_before_tax),
               "Equal to operating profit, because this model has no loan interest or depreciation lines."),
        Metric("Estimated tax", m(result.tax) if has_tax else "Not included",
               help="Applied only to positive profit, at the rate you entered." if has_tax else "No tax rate was entered."),
        Metric("Profit after tax", m(result.profit_after_tax), tone(result.profit_after_tax), PROFIT_HELP),
    ])

    break_even_section = Section("Break-even", [
        Metric("Break-even monthly revenue", m(result.break_even_revenue) if result.break_even_revenue is not None else "Not reachable",
               help=result.break_even_note),
        Metric("Contribution margin", format_percent(None if result.contribution_margin_ratio is None else result.contribution_margin_ratio * 100),
               help="Share of each sale left after direct costs to pay fixed costs."),
        Metric("Margin of safety", format_percent(result.margin_of_safety_pct), tone(result.margin_of_safety_pct),
               "How far revenue could fall before the business stops covering its costs."),
    ], intro="Assumes direct costs move in proportion to revenue and operating expenses stay fixed.")

    annual_section = Section("12-month forecast totals", [
        Metric("Forecast revenue (12 months)", m(result.annual_revenue)),
        Metric("Forecast costs (12 months)", m(result.annual_costs)),
        Metric("Forecast profit before tax", m(result.annual_profit_before_tax), tone(result.annual_profit_before_tax)),
        Metric("Forecast profit after tax", m(result.annual_profit_after_tax) if has_tax else "Tax not included",
               tone(result.annual_profit_after_tax) if has_tax else "neutral"),
    ])

    labels = [month.label for month in result.forecast]
    charts = [
        Chart("Revenue versus expenses (12-month forecast)", "bar", labels, [
            Series("Revenue", [mo.revenue for mo in result.forecast], "blue"),
            Series("Total expenses", [mo.direct_costs + mo.operating_expenses for mo in result.forecast], "slate"),
        ], "Monthly forecast revenue compared with direct costs plus operating expenses."),
        Chart("Projected monthly profit before tax", "bar", labels, [
            Series("Profit before tax", [mo.profit_before_tax for mo in result.forecast], "auto"),
        ], "Green bars are forecast profits, red bars are forecast losses."),
    ]

    forecast_table = Table(
        "12-month forecast",
        ["Month", "Revenue", "Direct costs", "Gross profit", "Operating expenses", "Profit before tax", "Cumulative profit"],
        [[mo.label, m(mo.revenue), m(mo.direct_costs), m(mo.gross_profit), m(mo.operating_expenses),
          m(mo.profit_before_tax), m(mo.cumulative_profit)] for mo in result.forecast]
        + [["Total", m(result.annual_revenue), m(sum(mo.direct_costs for mo in result.forecast)),
            m(sum(mo.gross_profit for mo in result.forecast)), m(sum(mo.operating_expenses for mo in result.forecast)),
            m(result.annual_profit_before_tax), ""]],
        note="Forecast figures, not actual results.",
        row_tones=[tone(mo.profit_before_tax) for mo in result.forecast] + ["neutral"],
        total_row=True,
    )
    breakdown = Table(
        "Monthly cost breakdown", ["Cost", "Type", "Amount", "Share of revenue"],
        [[label, "Direct" if kind == "direct" else "Operating", m(amount),
          format_percent(None if result.total_revenue == 0 else amount / result.total_revenue * 100)]
         for label, amount, kind in result.expense_lines],
    )
    income = Table("Monthly income", ["Income", "Amount"], [[label, m(amount)] for label, amount in result.revenue_lines])

    # --- Scenarios -------------------------------------------------------------
    adjustments = read_adjustments(data)
    scenario_results = {key: calculate(inputs.adjusted(adj)) for key, adj in adjustments.items()}
    scenarios = scenario_table(SCENARIO_NAMES, scenario_results, [
        ("Monthly revenue", lambda r: m(r.total_revenue)),
        ("Monthly costs", lambda r: m(r.total_direct_costs + r.total_operating_expenses)),
        (net_label, lambda r: m(r.profit_after_tax)),
        ("Net profit margin", lambda r: format_percent(r.net_margin_pct)),
        ("12-month profit before tax", lambda r: m(r.annual_profit_before_tax)),
        ("Break-even monthly sales", lambda r: m(r.break_even_revenue) if r.break_even_revenue is not None else "Not reachable"),
    ], adjustments, "Growth change (points)")

    # --- Assumptions -------------------------------------------------------------
    def opt_pct(value, missing):
        return format_percent(value, 2) if value is not None else missing

    assumptions = [
        ("Business name", inputs.business_name),
        ("Figures entered as", "Typical monthly amounts"),
        ("Forecast start", inputs.forecast_start.strftime("%B %Y") if inputs.forecast_start else "Not specified (months numbered 1 to 12)"),
        ("Monthly revenue growth", opt_pct(inputs.revenue_growth_pct, "None (flat revenue)")),
        ("Monthly operating expense growth", opt_pct(inputs.expense_growth_pct, "None (flat expenses)")),
        ("Tax rate on profit", opt_pct(inputs.tax_rate_pct, "Not included")),
        ("Break-even method", "Contribution margin: direct costs vary with sales, operating expenses are fixed"),
    ]
    not_included = [label for key, label in (
        ("salaries", "Salaries"), ("rent", "Rent"), ("utilities", "Utilities"), ("marketing", "Marketing"),
        ("transport", "Transport"), ("software_admin", "Software and admin"), ("other_operating", "Other operating"),
    ) if not inputs.operating.get(key)]
    if not_included:
        assumptions.append(("Expense lines left blank (treated as none)", ", ".join(not_included)))

    warnings = []
    if result.total_revenue == 0:
        warnings.append("Revenue is zero, so margins and break-even cannot be calculated.")
    if result.profit_after_tax < 0:
        warnings.append("At these figures the business makes a monthly loss. Review prices, direct costs and fixed expenses.")

    return Report(
        model_label="Business Financial Model",
        headline=headline,
        sections=[profit_section, break_even_section, annual_section],
        charts=charts,
        tables=[income, breakdown, forecast_table],
        scenario_table=scenarios,
        assumptions=assumptions,
        explanations=[
            ("Profit is not the same as cash",
             "A profitable business can still run short of cash. Customers may pay late, stock may be bought "
             "in advance, and loan repayments or equipment purchases use cash without appearing as monthly expenses here. "
             "Keep a separate eye on your bank balance."),
            ("Break-even", "Break-even sales is the monthly revenue at which total included costs equal revenue, "
             "so there is neither profit nor loss."),
        ],
        warnings=warnings,
        limitations=[
            "Uses typical monthly figures; seasonal swings are not modelled.",
            "Loan interest, depreciation and one-off purchases are not included.",
            "Tax is a simple estimate on positive profit and is not tax advice.",
        ],
    )
