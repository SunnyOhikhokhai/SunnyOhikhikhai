"""Turns a Startup model result into a presentable Report."""
from ..common.money import format_number, format_percent
from ..common.report import Chart, Formatter, Metric, Report, Section, Series, Table, scenario_table, tone
from ..common.scenarios import read_adjustments
from .calculations import LAUNCH_COST_FIELDS, StartupInputs, calculate

SCENARIO_NAMES = {"conservative": "Conservative", "expected": "Expected", "optimistic": "Optimistic"}


def runway_text(result) -> str:
    if result.runway_months is None:
        return f"More than {len(result.months)} months"
    if result.runway_months == 0:
        return "Cash runs out at launch"
    return f"{result.runway_months} month{'s' if result.runway_months != 1 else ''}"


def break_even_text(result) -> str:
    if result.break_even_month is None:
        return "Not within forecast"
    return f"Month {result.break_even_month.index} ({result.break_even_month.label})"


def build_report(data: dict, fmt: Formatter) -> Report:
    inputs = StartupInputs.from_dict(data)
    result = calculate(inputs)
    m = fmt.money
    horizon = len(result.months)

    runway_tone = "positive" if result.runway_months is None else "negative"
    headline = [
        Metric("Total launch costs", m(result.total_launch_costs), "neutral", "One-off costs paid before or at launch."),
        Metric("Estimated cash runway", runway_text(result), runway_tone,
               "How long your available cash may last at the projected spending rate, using the month-by-month forecast."),
        Metric("Break-even month", break_even_text(result), "positive" if result.break_even_month else "negative",
               "The first month in which revenue covers all monthly costs, including loan interest."),
        Metric("Additional funding needed", m(result.additional_funding_needed),
               "negative" if result.additional_funding_needed > 0 else "positive",
               "Extra cash needed to stop the bank balance going below zero during the forecast."),
    ]

    funding_section = Section("Funding", [
        Metric("Funding available", m(result.total_funding_available),
               help="Initial capital plus planned funding and any loan."),
        Metric("Cash after launch costs", m(result.cash_after_launch), tone(result.cash_after_launch)),
        Metric("Total funding required", m(result.total_funding_required),
               help="Launch costs plus the largest running total of monthly operating losses. Excludes loan repayments."),
        Metric("Lowest cash balance", m(result.lowest_cash), tone(result.lowest_cash),
               "The lowest point of your bank balance in the forecast."),
        Metric("Monthly loan repayment", m(result.monthly_loan_payment) if result.monthly_loan_payment is not None else "No loan",
               help="Fixed monthly instalment covering interest and principal."),
    ])
    first, last = result.months[0], result.months[-1]
    trading_section = Section("Trading", [
        Metric("Revenue in month 1", m(first.revenue)),
        Metric(f"Revenue in month {horizon}", m(last.revenue)),
        Metric("Monthly fixed costs", m(inputs.fixed_costs), help="Operating expenses, staff and marketing."),
        Metric("Average monthly burn before break-even", m(result.average_burn_before_break_even) if result.average_burn_before_break_even is not None else "No burn",
               help="Cash burn is the amount of cash the business uses up in a month when costs exceed income."),
        Metric("Break-even customers per month", format_number(result.break_even_customers) if result.break_even_customers is not None else "Not reachable",
               help="Customers needed each month to cover fixed costs (excluding loan interest)."),
        Metric(f"Total operating profit ({horizon} months)", m(result.total_operating_profit), tone(result.total_operating_profit)),
    ])

    labels = [mo.label for mo in result.months]
    charts = [
        Chart("Startup cash balance", "line", ["Launch"] + labels, [
            Series("Closing cash", [result.cash_after_launch] + [mo.closing_cash for mo in result.months], "navy"),
        ], "Bank balance at the end of each month. Below the zero line means cash has run out."),
        Chart("Revenue versus expenses", "bar", labels, [
            Series("Revenue", [mo.revenue for mo in result.months], "blue"),
            Series("Expenses", [mo.direct_costs + mo.fixed_costs + mo.loan_interest for mo in result.months], "slate"),
        ], "Monthly revenue compared with direct costs, fixed costs and loan interest."),
        Chart("Monthly net cash flow", "bar", labels, [
            Series("Net cash flow", [mo.net_cash_flow for mo in result.months], "auto"),
        ], "Cash in minus cash out each month, including funding received."),
    ]

    table = Table(
        f"{horizon}-month cash forecast",
        ["Month", "Customers", "Revenue", "Direct costs", "Fixed costs", "Loan payment", "Funding in", "Net cash flow", "Closing cash"],
        [["Launch", "", "", m(result.total_launch_costs) + " launch", "", "", "", "", m(result.cash_after_launch)]]
        + [[mo.label, format_number(mo.customers), m(mo.revenue), m(mo.direct_costs), m(mo.fixed_costs),
            m(mo.loan_interest + mo.loan_principal), m(mo.funding_in), m(mo.net_cash_flow), m(mo.closing_cash)]
           for mo in result.months],
        note="Forecast figures based on your assumptions, not actual results.",
        row_tones=[tone(result.cash_after_launch) if result.cash_after_launch < 0 else "neutral"]
        + ["negative" if mo.closing_cash < 0 else "neutral" for mo in result.months],
    )
    launch_table = Table("Launch costs", ["Cost", "Amount"],
                         [[label, m(inputs.launch_costs.get(key))] for key, label in LAUNCH_COST_FIELDS if inputs.launch_costs.get(key)]
                         + [["Total launch costs", m(result.total_launch_costs)]], total_row=True)

    adjustments = read_adjustments(data)
    scenario_results = {key: calculate(inputs.adjusted(adj)) for key, adj in adjustments.items()}
    scenarios = scenario_table(SCENARIO_NAMES, scenario_results, [
        (f"Revenue in month {horizon}", lambda r: m(r.months[-1].revenue)),
        ("Cash runway", runway_text),
        ("Break-even month", break_even_text),
        ("Lowest cash balance", lambda r: m(r.lowest_cash)),
        ("Additional funding needed", lambda r: m(r.additional_funding_needed)),
    ], adjustments, "Growth change (points)")

    def opt(value, formatter, missing):
        return formatter(value) if value is not None else missing

    assumptions = [
        ("Startup name", inputs.startup_name),
        ("Business description", inputs.description or "Not provided"),
        ("Launch month", inputs.launch_date.strftime("%B %Y") if inputs.launch_date else "Not specified"),
        ("Initial capital", m(inputs.initial_capital)),
        ("Customers in month 1", format_number(inputs.customers_month_1, 2)),
        ("Average revenue per customer", m(inputs.revenue_per_customer)),
        ("Monthly customer growth", opt(inputs.customer_growth_pct, lambda v: format_percent(v, 2), "None")),
        ("Direct costs", opt(inputs.direct_cost_pct, lambda v: format_percent(v, 2) + " of revenue", "Not included")),
        ("Monthly operating expenses", m(inputs.monthly_operating_expenses)),
        ("Monthly staff costs", opt(inputs.staff_costs, m, "Not included")),
        ("Monthly marketing budget", opt(inputs.marketing_budget, m, "Not included")),
        ("Planned funding", f"{m(inputs.planned_funding)} in month {inputs.planned_funding_month}" if inputs.planned_funding else "None"),
        ("Loan", f"{m(inputs.loan_amount)} at {format_percent(inputs.loan_interest_pct, 2)} a year over {inputs.loan_term_months} months"
         if inputs.loan_amount else "None"),
        ("Forecast length", f"{horizon} months"),
    ]

    warnings = []
    if result.cash_after_launch < 0:
        warnings.append("Launch costs are higher than the funding available at launch.")
    if result.runway_months is not None:
        warnings.append(f"Cash is forecast to run out after {runway_text(result).lower()}. Consider raising "
                        f"at least {m(result.additional_funding_needed)} more, cutting costs or growing faster.")
    if result.break_even_customers is None:
        warnings.append("Direct costs take up all revenue per customer, so more customers will not reach break-even.")

    return Report(
        model_label="Startup Financial Model",
        headline=headline,
        sections=[funding_section, trading_section],
        charts=charts,
        tables=[launch_table, table],
        scenario_table=scenarios,
        assumptions=assumptions,
        explanations=[
            ("Cash runway", "Cash runway is how long your available cash may last at the projected spending rate. "
             "FINPLAN works it out month by month, so growing revenue and changing costs are taken into account."),
            ("Cash burn", "Cash burn is the amount of cash the business uses up in a month when what goes out is more than what comes in."),
            ("Break-even", "Break-even is reached when monthly revenue covers all monthly costs. "
             "Reaching break-even does not mean earlier losses have been recovered."),
        ],
        warnings=warnings,
        limitations=[
            "Customers pay in the month of sale; late payments are not modelled.",
            "Tax, VAT and inflation are not included.",
            "Loan repayments start in the first trading month with no grace period.",
        ],
    )
