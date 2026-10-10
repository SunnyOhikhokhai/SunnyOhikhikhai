"""Input form for the Startup Financial Model."""
from decimal import Decimal

from django import forms

from ..common.forms import ModelInputForm, Step, money, percent, quantity, whole
from ..common.scenarios import ExtraLever

HORIZON_CHOICES = [(12, "12 months"), (24, "24 months"), (36, "36 months")]


class StartupForm(ModelInputForm):
    startup_name = forms.CharField(label="Startup name", max_length=120)
    description = forms.CharField(
        label="What does the business do?", required=False, max_length=500,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="One or two sentences. This appears on your report.",
    )
    launch_date = forms.DateField(
        label="Planned launch month", required=False,
        help_text="Used to label forecast months. Pick any day in that month.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    initial_capital = money(
        "Initial capital available", required=True, placeholder="e.g. 10000000",
        help_text="Cash you (and any co-founders) can put in at launch. Enter 0 if none.",
    )
    equipment_setup = money("Equipment and setup costs", help_text="Machines, furniture, computers, shop fit-out.")
    registration_fees = money("Registration and professional fees", help_text="Company registration, permits, legal and accounting set-up.")
    initial_inventory = money("Initial inventory", help_text="Stock or materials bought before you start selling.")
    other_launch_costs = money("Other launch costs", help_text="Deposits, website build, launch events and similar one-off costs.")
    customers_month_1 = quantity(
        "Expected paying customers in month 1", required=True, placeholder="e.g. 50",
        help_text="How many customers (or orders) you expect in your first month of trading.",
    )
    revenue_per_customer = money(
        "Average revenue per customer per month", required=True, placeholder="e.g. 15000",
        help_text="What each customer spends with you in a month, on average.",
    )
    customer_growth_pct = percent(
        "Monthly customer growth (%)", min_value="-50", max_value="200", placeholder="e.g. 8",
        help_text="How quickly you expect customer numbers to grow each month.",
    )
    direct_cost_pct = percent(
        "Direct costs as % of revenue", placeholder="e.g. 35",
        help_text="Materials, packaging or delivery costs per sale, as a share of the price.",
    )
    monthly_operating_expenses = money(
        "Monthly operating expenses", required=True, placeholder="e.g. 800000",
        help_text="Rent, utilities, software, transport and other running costs. Enter 0 if none.",
    )
    staff_costs = money("Monthly staff costs", help_text="Salaries and wages for your team.")
    marketing_budget = money("Monthly marketing budget", help_text="Adverts, promotions and social media spend.")
    planned_funding = money(
        "Additional funding received or planned",
        help_text="Grants or investment you expect to receive (not loans). Leave blank if none.",
    )
    planned_funding_month = whole(
        "Month the funding arrives", min_value=0, max_value=36,
        help_text="0 means at launch, 1 means the first trading month, and so on.",
    )
    loan_amount = money("Loan amount", help_text="Leave blank if you are not borrowing.")
    loan_interest_pct = percent("Loan interest rate (% per year)", max_value="200", help_text="Annual interest rate on the loan.")
    loan_term_months = whole("Loan repayment term (months)", min_value=1, max_value=360,
                             help_text="Repaid in equal monthly instalments starting in month 1.")
    forecast_months = forms.TypedChoiceField(
        label="Forecast length", choices=HORIZON_CHOICES, coerce=int, initial=12,
        help_text="Longer forecasts help when break-even is more than a year away.",
    )

    extra_lever = ExtraLever(
        label="Customer growth change (percentage points)",
        help="Added to monthly customer growth, e.g. −2 turns 8% into 6%.",
        unit="points", conservative=Decimal("-2"), optimistic=Decimal("2"),
        min_value=Decimal("-50"), max_value=Decimal("50"),
    )

    steps = (
        Step("About your startup", "Tell us what you are building.",
             fields=("project_name", "startup_name", "currency"), advanced=("description", "launch_date")),
        Step("Launch costs and capital", "One-off costs to get started and the money you have available.",
             fields=("initial_capital", "equipment_setup", "registration_fees"),
             advanced=("initial_inventory", "other_launch_costs"), advanced_title="More launch costs"),
        Step("Customers and revenue", "Estimate demand. Be realistic – early months are often slower than hoped.",
             fields=("customers_month_1", "revenue_per_customer", "customer_growth_pct"), advanced=("direct_cost_pct",)),
        Step("Monthly running costs", "What it costs to keep the business running each month.",
             fields=("monthly_operating_expenses", "staff_costs", "marketing_budget"), advanced=("forecast_months",),
             advanced_title="Forecast length"),
        Step("Funding and loans", "Optional. Add investment, grants or a loan.",
             fields=("planned_funding", "planned_funding_month"),
             advanced=("loan_amount", "loan_interest_pct", "loan_term_months"), advanced_title="Add a loan"),
        Step("Scenarios", "Test slower or faster growth and higher or lower costs.", scenarios=True),
    )

    def clean(self):
        cleaned = super().clean()
        loan = cleaned.get("loan_amount")
        if loan:
            if cleaned.get("loan_interest_pct") is None:
                self.add_error("loan_interest_pct", "Enter the loan interest rate (use 0 for an interest-free loan).")
            if not cleaned.get("loan_term_months"):
                self.add_error("loan_term_months", "Enter how many months the loan will be repaid over.")
        funding = cleaned.get("planned_funding")
        month = cleaned.get("planned_funding_month")
        if funding:
            if month is None:
                self.add_error("planned_funding_month", "Tell us when this funding arrives (0 = at launch).")
            elif cleaned.get("forecast_months") and month > cleaned["forecast_months"]:
                self.add_error("planned_funding_month", "This month is after the end of the forecast.")
        return cleaned
