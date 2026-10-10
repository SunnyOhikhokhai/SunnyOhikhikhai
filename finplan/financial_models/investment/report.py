"""Turns an Investment model result into a presentable Report."""
from ..common.money import format_percent
from ..common.report import Chart, Formatter, Metric, Report, Section, Series, Table, scenario_table, tone
from ..common.scenarios import read_adjustments
from .calculations import INVESTMENT_TYPES, InvestmentInputs, calculate

SCENARIO_NAMES = {"conservative": "Worst case", "expected": "Expected case", "optimistic": "Best case"}


def build_report(data: dict, fmt: Formatter) -> Report:
    inputs = InvestmentInputs.from_dict(data)
    result = calculate(inputs)
    m = fmt.money

    headline = [
        Metric("Total capital invested", m(result.total_capital), "neutral", "Initial investment plus any additional contributions."),
        Metric("Net investment profit", m(result.net_profit), tone(result.net_profit),
               "Everything you get back minus everything you put in and pay out, over the whole period."),
        Metric("Simple ROI (whole period)", format_percent(result.roi_pct), tone(result.roi_pct),
               "Net profit ÷ capital invested. It ignores how long the money is tied up."),
        Metric("Internal rate of return (IRR)", format_percent(result.irr_pct) if result.irr_pct is not None else "Not available",
               tone(result.irr_pct), result.irr_note),
    ]

    returns = Section("Returns", [
        Metric("Simple ROI (whole period)", format_percent(result.roi_pct), tone(result.roi_pct),
               "Total return over the full investment period, not per year."),
        Metric("Annualised return", format_percent(result.annualised_return_pct) if result.annualised_return_pct is not None else "Not shown",
               tone(result.annualised_return_pct), result.annualised_note),
        Metric("IRR (per year)", format_percent(result.irr_pct) if result.irr_pct is not None else "Not available",
               tone(result.irr_pct), result.irr_note),
        Metric("Net present value (NPV)", m(result.npv) if result.npv is not None else "Add a discount rate",
               tone(result.npv),
               "Today's value of all future cash flows minus what you invest. Positive means the investment beats your discount rate."
               if result.npv is not None else "NPV needs a discount rate, which you can add in the inputs."),
        Metric("Payback", f"Year {result.payback_year}" if result.payback_year else "Not within the period",
               "positive" if result.payback_year else "negative", "The year in which cumulative cash flow turns positive."),
    ])
    totals = Section("Totals over the investment period", [
        Metric("Total projected income", m(result.total_income)),
        Metric("Total projected expenses", m(result.total_expenses), help="Operating expenses, financing costs and tax."),
        Metric("Expected exit proceeds", m(result.exit_value)),
        Metric("Estimated tax", m(result.total_tax) if inputs.tax_rate_pct is not None else "Not included"),
    ])

    labels = [f"Year {y.year}" for y in result.years]
    charts = [
        Chart("Yearly investment cash flows", "bar", labels, [Series("Cash flow", result.cash_flows, "auto")],
              "Year 0 is the initial investment (negative). Later years show net cash received, including the exit value."),
        Chart("Cumulative cash position", "line", labels, [Series("Cumulative", [y.cumulative for y in result.years], "navy")],
              "Running total of money in and out. Crossing zero is the payback point."),
    ]
    table = Table(
        "Yearly cash flows",
        ["Year", "Money invested", "Income", "Expenses", "Financing", "Tax", "Exit value", "Net cash flow", "Cumulative"],
        [[f"Year {y.year}", m(y.contribution), m(y.income), m(y.expenses), m(y.financing), m(y.tax),
          m(y.exit_value), m(y.cash_flow), m(y.cumulative)] for y in result.years],
        note="Projected figures based on your assumptions. Returns are not guaranteed.",
        row_tones=[tone(y.cash_flow) for y in result.years],
    )

    adjustments = read_adjustments(data)
    scenario_results = {key: calculate(inputs.adjusted(adj)) for key, adj in adjustments.items()}
    scenarios = scenario_table(SCENARIO_NAMES, scenario_results, [
        ("Net investment profit", lambda r: m(r.net_profit)),
        ("Simple ROI", lambda r: format_percent(r.roi_pct)),
        ("IRR", lambda r: format_percent(r.irr_pct) if r.irr_pct is not None else "Not available"),
        ("NPV", lambda r: m(r.npv) if r.npv is not None else "No discount rate"),
    ], adjustments, "Exit value change (%)")

    def opt(value, formatter, missing):
        return formatter(value) if value is not None else missing

    assumptions = [
        ("Investment name", inputs.investment_name),
        ("Type", dict(INVESTMENT_TYPES).get(inputs.investment_type, inputs.investment_type)),
        ("Initial investment", m(inputs.initial_investment)),
        ("Duration", f"{inputs.duration_years} year(s)"),
        ("Annual income (year 1)", m(inputs.annual_income)),
        ("Annual income growth", opt(inputs.income_growth_pct, lambda v: format_percent(v, 2), "None")),
        ("Annual expenses", opt(inputs.annual_expenses, m, "Not included")),
        ("Additional contribution per year", opt(inputs.additional_contribution, m, "None")),
        ("Annual financing costs", opt(inputs.annual_financing_costs, m, "None")),
        ("Exit value", opt(inputs.exit_value, m, "None (no sale value assumed)")),
        ("Tax rate", opt(inputs.tax_rate_pct, lambda v: format_percent(v, 2), "Not included")),
        ("Discount rate", opt(inputs.discount_rate_pct, lambda v: format_percent(v, 2), "Not provided (no NPV)")),
        ("Timing", "Yearly cash flows; income and costs at year end; exit at the end of the final year"),
    ]

    warnings = []
    if result.net_profit < 0:
        warnings.append("At these assumptions you would get back less than you put in.")
    if result.exit_value == 0 and inputs.investment_type == "property":
        warnings.append("No exit value is included. Property investments usually have a resale value – check whether it should be added.")

    return Report(
        model_label="Investment Financial Model",
        headline=headline,
        sections=[returns, totals],
        charts=charts,
        tables=[table],
        scenario_table=scenarios,
        assumptions=assumptions,
        explanations=[
            ("Simple ROI, annualised return and IRR are different",
             "Simple ROI is the total gain over the whole period. Annualised return spreads that gain evenly over each year. "
             "IRR also considers when each amount is paid or received, so money received earlier counts for more. "
             "Do not compare one directly with another."),
            ("No guarantees", "All returns shown are estimates based on your assumptions. Real investments can lose money."),
        ],
        warnings=warnings,
        limitations=[
            "Uses yearly periods; monthly timing is not modelled.",
            "Tax on the exit gain is not included.",
            "Inflation and currency movements are not included.",
        ],
    )
