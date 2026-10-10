"""
Investment Financial Model – calculation engine.

Cash flows are yearly. Year 0 is today (the initial investment). Years 1…N
receive income and pay expenses; the exit value arrives at the end of year N.

Yearly cash flow (year t ≥ 1)
-----------------------------
Income           = Annual income × (1 + income growth)^(t−1)
Taxable profit   = Income − Operating expenses − Financing costs
Tax              = max(Taxable profit, 0) × Tax rate
Cash flow        = Income − Expenses − Financing − Tax − Additional contribution
                   (+ Exit value in the final year)

Summary measures
----------------
Total capital invested = Initial investment + Additional contributions
Net investment profit  = Sum of all yearly cash flows including year 0
                       = Income − Expenses − Financing − Tax + Exit value − Capital invested
Simple ROI (%)         = Net profit ÷ Total capital invested × 100
                         (whole period, ignores timing)
Annualised return (%)  = ((Capital + Net profit) ÷ Capital)^(1 ÷ years) − 1
                         Only when all capital is invested at the start; it
                         treats all money as received at the end.
NPV                    = Σ Cash flowₜ ÷ (1 + discount rate)ᵗ
IRR                    = discount rate at which NPV = 0 (accounts for timing)
Payback year           = first year in which cumulative cash flow is ≥ 0
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from ..common.finance import annualised_return, grow, irr, npv, sign_changes
from ..common.inputs import dec, integer, text
from ..common.money import HUNDRED, ZERO, or_zero, pct_to_fraction, percentage
from ..common.scenarios import ScenarioAdjustment, scale

INVESTMENT_TYPES = [
    ("business", "Business investment"),
    ("property", "Property investment"),
    ("other", "Other cash-flow investment"),
]


@dataclass(frozen=True)
class InvestmentInputs:
    investment_name: str
    investment_type: str
    initial_investment: Decimal
    duration_years: int
    annual_income: Decimal
    additional_contribution: Decimal | None = None
    income_growth_pct: Decimal | None = None
    annual_expenses: Decimal | None = None
    exit_value: Decimal | None = None
    annual_financing_costs: Decimal | None = None
    tax_rate_pct: Decimal | None = None
    discount_rate_pct: Decimal | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "InvestmentInputs":
        return cls(
            investment_name=text(data, "investment_name", text(data, "project_name")),
            investment_type=text(data, "investment_type", "other"),
            initial_investment=dec(data, "initial_investment", required=True, label="Initial investment"),
            duration_years=integer(data, "duration_years", required=True, label="Investment duration"),
            annual_income=dec(data, "annual_income", required=True, label="Expected annual income"),
            additional_contribution=dec(data, "additional_contribution"),
            income_growth_pct=dec(data, "income_growth_pct"),
            annual_expenses=dec(data, "annual_expenses"),
            exit_value=dec(data, "exit_value"),
            annual_financing_costs=dec(data, "annual_financing_costs"),
            tax_rate_pct=dec(data, "tax_rate_pct"),
            discount_rate_pct=dec(data, "discount_rate_pct"),
        )

    def adjusted(self, adj: ScenarioAdjustment) -> "InvestmentInputs":
        """Revenue % changes income; cost % changes expenses and financing; extra changes the exit value (%)."""
        if adj.is_neutral:
            return self
        return replace(
            self,
            annual_income=scale(self.annual_income, adj.revenue_pct),
            annual_expenses=scale(self.annual_expenses, adj.cost_pct),
            annual_financing_costs=scale(self.annual_financing_costs, adj.cost_pct),
            exit_value=scale(self.exit_value, adj.extra),
        )


@dataclass(frozen=True)
class InvestmentYear:
    year: int
    contribution: Decimal
    income: Decimal
    expenses: Decimal
    financing: Decimal
    tax: Decimal
    exit_value: Decimal
    cash_flow: Decimal
    cumulative: Decimal


@dataclass(frozen=True)
class InvestmentResult:
    years: list[InvestmentYear]
    cash_flows: list[Decimal]
    total_capital: Decimal
    total_income: Decimal
    total_expenses: Decimal  # operating + financing + tax
    total_tax: Decimal
    exit_value: Decimal
    net_profit: Decimal
    roi_pct: Decimal | None
    annualised_return_pct: Decimal | None
    annualised_note: str
    npv: Decimal | None
    irr_pct: Decimal | None
    irr_note: str
    payback_year: int | None


def calculate(inputs: InvestmentInputs) -> InvestmentResult:
    n = inputs.duration_years
    growth = pct_to_fraction(inputs.income_growth_pct)
    tax_rate = pct_to_fraction(inputs.tax_rate_pct)
    contribution = or_zero(inputs.additional_contribution)
    expenses = or_zero(inputs.annual_expenses)
    financing = or_zero(inputs.annual_financing_costs)
    exit_value = or_zero(inputs.exit_value)

    cash_flows = [-inputs.initial_investment]
    years = [InvestmentYear(0, inputs.initial_investment, ZERO, ZERO, ZERO, ZERO, ZERO,
                            -inputs.initial_investment, -inputs.initial_investment)]
    cumulative = -inputs.initial_investment
    payback = None
    for t in range(1, n + 1):
        income = grow(inputs.annual_income, growth, t - 1)
        tax = max(income - expenses - financing, ZERO) * tax_rate
        year_exit = exit_value if t == n else ZERO
        flow = income - expenses - financing - tax - contribution + year_exit
        cumulative += flow
        cash_flows.append(flow)
        years.append(InvestmentYear(t, contribution, income, expenses, financing, tax, year_exit, flow, cumulative))
        if payback is None and cumulative >= 0:
            payback = t

    total_capital = inputs.initial_investment + contribution * n
    total_income = sum((y.income for y in years), ZERO)
    total_tax = sum((y.tax for y in years), ZERO)
    total_expenses = sum((y.expenses + y.financing + y.tax for y in years), ZERO)
    net_profit = sum(cash_flows, ZERO)

    # Annualised return – only meaningful when all capital goes in at the start.
    if contribution > 0:
        annualised, annual_note = None, ("Not shown because money is added during the investment. "
                                         "Use IRR, which accounts for when each amount is paid or received.")
    else:
        rate = annualised_return(total_capital, total_capital + net_profit, Decimal(n))
        annualised = None if rate is None else rate * HUNDRED
        annual_note = ("Spreads the total return evenly over each year, as if all money were received at the end."
                       if rate is not None else "Cannot be calculated because more than the capital invested is lost.")

    npv_value = None
    if inputs.discount_rate_pct is not None:
        npv_value = npv(pct_to_fraction(inputs.discount_rate_pct), cash_flows)

    irr_value = irr(cash_flows)
    if irr_value is None:
        irr_note = "No IRR exists for these cash flows (they never move from negative to positive, or vice versa)."
    elif sign_changes(cash_flows) > 1:
        irr_note = "Cash flows change direction more than once, so more than one IRR may exist. Treat this figure with caution."
    else:
        irr_note = "The yearly return that makes the investment break even in today's money, taking timing into account."

    return InvestmentResult(
        years=years,
        cash_flows=cash_flows,
        total_capital=total_capital,
        total_income=total_income,
        total_expenses=total_expenses,
        total_tax=total_tax,
        exit_value=exit_value,
        net_profit=net_profit,
        roi_pct=percentage(net_profit, total_capital),
        annualised_return_pct=annualised,
        annualised_note=annual_note,
        npv=npv_value,
        irr_pct=None if irr_value is None else irr_value * HUNDRED,
        irr_note=irr_note,
        payback_year=payback,
    )
