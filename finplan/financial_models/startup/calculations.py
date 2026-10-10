"""
Startup Financial Model – calculation engine.

The model runs a month-by-month cash forecast. Month 0 is launch: launch
costs are paid and starting funds arrive. Months 1…N are trading months.

Formulas (month m ≥ 1)
----------------------
Customers           = Customers in month 1 × (1 + customer growth)^(m−1)
Revenue             = Customers × Average revenue per customer
Direct costs        = Revenue × Direct cost %
Fixed costs         = Monthly operating expenses + Staff costs + Marketing budget
Loan payment        = Level (annuity) payment over the loan term; split into
                      interest (balance × monthly rate) and principal
Operating profit    = Revenue − Direct costs − Fixed costs − Loan interest
Cash from operations= Operating profit − Loan principal repaid
Net cash flow       = Cash from operations + Funding received that month
Closing cash        = Opening cash + Net cash flow
Cash burn           = −Cash from operations, when it is negative

Cash runway
    Uses the month-by-month forecast, not a single division. Runway is the
    number of trading months completed before the closing cash balance first
    falls below zero. If cash never goes negative, runway lasts beyond the
    forecast period.

Break-even
    Break-even month = first month whose operating profit is zero or more.
    Break-even customers per month = Fixed costs ÷ (Revenue per customer × (1 − Direct cost %))

Funding
    Total funding required = Launch costs + the largest cumulative operating
                             loss (revenue − direct − fixed costs) over the forecast.
    Additional funding needed = the deepest negative closing cash balance,
                                after all planned funding and loan payments.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from ..common.finance import annuity_payment, grow
from ..common.inputs import a_date, dec, integer, month_label, text
from ..common.money import HUNDRED, ONE, ZERO, or_zero, pct_to_fraction, safe_divide
from ..common.scenarios import ScenarioAdjustment, scale

LAUNCH_COST_FIELDS = (
    ("equipment_setup", "Equipment and setup"),
    ("registration_fees", "Registration and professional fees"),
    ("initial_inventory", "Initial inventory"),
    ("other_launch_costs", "Other launch costs"),
)


@dataclass(frozen=True)
class StartupInputs:
    startup_name: str
    description: str
    launch_date: date | None
    initial_capital: Decimal
    launch_costs: dict[str, Decimal | None]
    customers_month_1: Decimal
    revenue_per_customer: Decimal
    customer_growth_pct: Decimal | None
    direct_cost_pct: Decimal | None
    monthly_operating_expenses: Decimal
    staff_costs: Decimal | None
    marketing_budget: Decimal | None
    planned_funding: Decimal | None
    planned_funding_month: int | None
    loan_amount: Decimal | None
    loan_interest_pct: Decimal | None
    loan_term_months: int | None
    forecast_months: int = 12

    @classmethod
    def from_dict(cls, data: dict) -> "StartupInputs":
        loan = dec(data, "loan_amount")
        has_loan = bool(loan and loan > 0)
        funding = dec(data, "planned_funding")
        return cls(
            startup_name=text(data, "startup_name", text(data, "project_name")),
            description=text(data, "description"),
            launch_date=a_date(data, "launch_date"),
            initial_capital=dec(data, "initial_capital", required=True, label="Initial capital available"),
            launch_costs={key: dec(data, key) for key, _ in LAUNCH_COST_FIELDS},
            customers_month_1=dec(data, "customers_month_1", required=True, label="Expected customers in month 1"),
            revenue_per_customer=dec(data, "revenue_per_customer", required=True, label="Average revenue per customer"),
            customer_growth_pct=dec(data, "customer_growth_pct"),
            direct_cost_pct=dec(data, "direct_cost_pct"),
            monthly_operating_expenses=dec(data, "monthly_operating_expenses", required=True, label="Monthly operating expenses"),
            staff_costs=dec(data, "staff_costs"),
            marketing_budget=dec(data, "marketing_budget"),
            planned_funding=funding,
            planned_funding_month=integer(data, "planned_funding_month", required=bool(funding), label="Month funding arrives") if funding else None,
            loan_amount=loan,
            loan_interest_pct=dec(data, "loan_interest_pct", required=has_loan, label="Loan interest rate"),
            loan_term_months=integer(data, "loan_term_months", required=has_loan, label="Loan term"),
            forecast_months=integer(data, "forecast_months") or 12,
        )

    @property
    def total_launch_costs(self) -> Decimal:
        return sum((or_zero(v) for v in self.launch_costs.values()), ZERO)

    @property
    def fixed_costs(self) -> Decimal:
        return self.monthly_operating_expenses + or_zero(self.staff_costs) + or_zero(self.marketing_budget)

    def adjusted(self, adj: ScenarioAdjustment) -> "StartupInputs":
        """Revenue % changes revenue per customer; cost % changes launch and fixed costs; extra changes growth (points)."""
        if adj.is_neutral:
            return self
        c = adj.cost_pct
        return replace(
            self,
            revenue_per_customer=scale(self.revenue_per_customer, adj.revenue_pct),
            launch_costs={k: scale(v, c) for k, v in self.launch_costs.items()},
            monthly_operating_expenses=scale(self.monthly_operating_expenses, c),
            staff_costs=scale(self.staff_costs, c),
            marketing_budget=scale(self.marketing_budget, c),
            customer_growth_pct=or_zero(self.customer_growth_pct) + adj.extra,
        )


@dataclass(frozen=True)
class StartupMonth:
    index: int
    label: str
    customers: Decimal
    revenue: Decimal
    direct_costs: Decimal
    fixed_costs: Decimal
    loan_interest: Decimal
    loan_principal: Decimal
    operating_profit: Decimal
    operating_cash_flow: Decimal
    funding_in: Decimal
    net_cash_flow: Decimal
    closing_cash: Decimal

    @property
    def burn(self) -> Decimal:
        return -self.operating_cash_flow if self.operating_cash_flow < 0 else ZERO


@dataclass(frozen=True)
class StartupResult:
    total_launch_costs: Decimal
    total_funding_available: Decimal
    cash_after_launch: Decimal
    months: list[StartupMonth]
    runway_months: int | None  # None = cash lasts beyond the forecast
    runs_out_label: str | None
    break_even_month: StartupMonth | None
    break_even_customers: Decimal | None
    total_funding_required: Decimal
    additional_funding_needed: Decimal
    lowest_cash: Decimal
    average_burn_before_break_even: Decimal | None
    monthly_loan_payment: Decimal | None
    total_revenue: Decimal
    total_costs: Decimal
    total_operating_profit: Decimal


def calculate(inputs: StartupInputs) -> StartupResult:
    horizon = inputs.forecast_months
    growth = pct_to_fraction(inputs.customer_growth_pct)
    direct_ratio = pct_to_fraction(inputs.direct_cost_pct)
    fixed = inputs.fixed_costs

    # --- Loan schedule -------------------------------------------------------------
    loan = or_zero(inputs.loan_amount)
    payment = None
    monthly_rate = ZERO
    if loan > 0:
        monthly_rate = or_zero(inputs.loan_interest_pct) / HUNDRED / 12
        payment = annuity_payment(loan, monthly_rate, inputs.loan_term_months)
    loan_balance = loan

    # --- Month 0: launch ---------------------------------------------------------------
    launch_costs = inputs.total_launch_costs
    funding_at_launch = or_zero(inputs.planned_funding) if inputs.planned_funding_month == 0 else ZERO
    cash = inputs.initial_capital + loan + funding_at_launch - launch_costs
    cash_after_launch = cash
    total_funding = inputs.initial_capital + loan + or_zero(inputs.planned_funding)

    months: list[StartupMonth] = []
    runway = None if cash >= 0 else 0
    cumulative_operating = -launch_costs
    lowest_cumulative = cumulative_operating
    lowest_cash = cash

    for m in range(1, horizon + 1):
        customers = grow(inputs.customers_month_1, growth, m - 1)
        revenue = customers * inputs.revenue_per_customer
        direct = revenue * direct_ratio
        interest = principal = ZERO
        if payment is not None and loan_balance > 0 and m <= inputs.loan_term_months:
            interest = loan_balance * monthly_rate
            principal = min(payment - interest, loan_balance)
            loan_balance -= principal
        operating_profit = revenue - direct - fixed - interest
        operating_cash = operating_profit - principal
        funding_in = or_zero(inputs.planned_funding) if inputs.planned_funding_month == m else ZERO
        net = operating_cash + funding_in
        cash += net
        months.append(StartupMonth(
            index=m, label=month_label(inputs.launch_date, m), customers=customers, revenue=revenue,
            direct_costs=direct, fixed_costs=fixed, loan_interest=interest, loan_principal=principal,
            operating_profit=operating_profit, operating_cash_flow=operating_cash, funding_in=funding_in,
            net_cash_flow=net, closing_cash=cash,
        ))
        if runway is None and cash < 0:
            runway = m - 1
        lowest_cash = min(lowest_cash, cash)
        cumulative_operating += revenue - direct - fixed
        lowest_cumulative = min(lowest_cumulative, cumulative_operating)

    break_even = next((mo for mo in months if mo.operating_profit >= 0), None)
    contribution = inputs.revenue_per_customer * (ONE - direct_ratio)
    break_even_customers = safe_divide(fixed, contribution) if contribution > 0 else None

    pre_break_even = [mo for mo in months if break_even is None or mo.index < break_even.index]
    burns = [mo.burn for mo in pre_break_even if mo.burn > 0]
    average_burn = sum(burns, ZERO) / len(burns) if burns else None

    runs_out_label = None
    if runway is not None:
        runs_out_label = "At launch" if runway == 0 else months[runway].label if runway < len(months) else None

    total_revenue = sum((mo.revenue for mo in months), ZERO)
    total_costs = sum((mo.direct_costs + mo.fixed_costs + mo.loan_interest for mo in months), ZERO)

    return StartupResult(
        total_launch_costs=launch_costs,
        total_funding_available=total_funding,
        cash_after_launch=cash_after_launch,
        months=months,
        runway_months=runway,
        runs_out_label=runs_out_label,
        break_even_month=break_even,
        break_even_customers=break_even_customers,
        total_funding_required=-lowest_cumulative if lowest_cumulative < 0 else ZERO,
        additional_funding_needed=-lowest_cash if lowest_cash < 0 else ZERO,
        lowest_cash=lowest_cash,
        average_burn_before_break_even=average_burn,
        monthly_loan_payment=payment,
        total_revenue=total_revenue,
        total_costs=total_costs,
        total_operating_profit=total_revenue - total_costs,
    )
