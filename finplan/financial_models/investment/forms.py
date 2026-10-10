"""Input form for the Investment Financial Model."""
from decimal import Decimal

from django import forms

from ..common.forms import ModelInputForm, Step, money, percent, whole
from ..common.scenarios import ExtraLever
from .calculations import INVESTMENT_TYPES


class InvestmentForm(ModelInputForm):
    scenario_names = {"conservative": "Worst case", "optimistic": "Best case"}

    investment_name = forms.CharField(label="Investment name", max_length=120)
    investment_type = forms.ChoiceField(label="Type of investment", choices=INVESTMENT_TYPES, initial="business")
    initial_investment = money(
        "Initial investment amount", required=True, placeholder="e.g. 20000000",
        help_text="The amount you put in at the start.",
    )
    duration_years = whole("Investment duration (years)", required=True, min_value=1, max_value=50, placeholder="e.g. 5",
                           help_text="How long you expect to hold the investment.")
    annual_income = money(
        "Expected annual income", required=True, placeholder="e.g. 4000000",
        help_text="Dividends, rent, profit share or interest you expect each year. Enter 0 if none.",
    )
    income_growth_pct = percent("Annual income growth (%)", min_value="-50", max_value="100",
                                help_text="How much the yearly income may grow each year.")
    annual_expenses = money("Annual operating or management expenses",
                            help_text="Management fees, maintenance, insurance and other yearly costs.")
    exit_value = money(
        "Expected final sale value or exit proceeds",
        help_text="What you expect to receive when you sell or exit at the end. Leave blank if nothing.",
    )
    additional_contribution = money("Additional contribution each year",
                                    help_text="Extra money you will add every year, if any.")
    annual_financing_costs = money("Annual financing costs", help_text="Yearly loan interest or fees if you borrow to invest.")
    tax_rate_pct = percent("Tax rate on yearly profit (%)", help_text="Optional. Applied to positive yearly income after expenses.")
    discount_rate_pct = percent(
        "Discount rate for NPV (% per year)", max_value="100", placeholder="e.g. 15",
        help_text="The yearly return you could earn elsewhere at similar risk. Needed for NPV.",
    )

    extra_lever = ExtraLever(
        label="Exit value change (%)",
        help="Change in the final sale value in this scenario.",
        unit="%", conservative=Decimal("-25"), optimistic=Decimal("15"),
        min_value=Decimal("-100"), max_value=Decimal("500"),
    )

    steps = (
        Step("About the investment", "Describe what you are assessing.",
             fields=("project_name", "investment_name", "currency", "investment_type")),
        Step("Money in", "How much you will invest and for how long.",
             fields=("initial_investment", "duration_years"), advanced=("additional_contribution",),
             advanced_title="Adding money over time"),
        Step("Income and costs", "What the investment may earn and cost each year.",
             fields=("annual_income", "annual_expenses", "exit_value"),
             advanced=("income_growth_pct", "annual_financing_costs", "tax_rate_pct"),
             advanced_title="Growth, financing and tax"),
        Step("Return analysis", "Optional. Add a discount rate to see net present value (NPV).",
             fields=("discount_rate_pct",)),
        Step("Scenarios", "Compare worst, expected and best cases.", scenarios=True),
    )
