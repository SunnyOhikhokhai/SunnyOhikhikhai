"""Input form for the Business Financial Model."""
from decimal import Decimal

from django import forms

from ..common.forms import LineItemSpec, ModelInputForm, Step, money, percent
from ..common.scenarios import ExtraLever


class BusinessForm(ModelInputForm):
    business_name = forms.CharField(label="Business name", max_length=120)
    forecast_start = forms.DateField(
        label="First month of the forecast",
        required=False,
        help_text="Used to label the 12-month forecast. Pick any day in that month.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    monthly_sales = money(
        "Monthly sales revenue", required=True, placeholder="e.g. 2500000",
        help_text="Money you typically receive from selling products or services in one month.",
    )
    other_income = money(
        "Other business income (monthly)",
        help_text="Income that is not from your main sales, such as commissions or equipment rental.",
    )
    direct_costs = money(
        "Cost of goods sold or direct service costs (monthly)", required=True, placeholder="e.g. 1000000",
        help_text="Costs that rise when you sell more: stock, raw materials, packaging, per-job labour. Enter 0 if none.",
    )
    salaries = money("Salaries and wages", help_text="Monthly staff pay, including your own salary if you draw one.")
    rent = money("Rent", help_text="Monthly rent for shops, offices or warehouses.")
    utilities = money("Utilities", help_text="Electricity, diesel, water, internet and phone.")
    marketing = money("Marketing", help_text="Adverts, promotions, social media and printing.")
    transport = money("Transport and logistics", help_text="Deliveries, fuel and travel for the business.")
    software_admin = money("Software and administrative expenses", help_text="Subscriptions, accounting, bank charges and stationery.")
    other_operating = money("Other operating expenses", help_text="Anything else you pay every month to run the business.")
    tax_rate_pct = percent(
        "Estimated tax rate on profit (%)", placeholder="e.g. 30",
        help_text="Optional. Leave blank to skip tax. Check the correct rate for your business with a tax adviser.",
    )
    revenue_growth_pct = percent(
        "Expected monthly revenue growth (%)", min_value="-50", max_value="100", placeholder="e.g. 2",
        help_text="How much revenue may grow each month. Use a negative number for an expected decline.",
    )
    expense_growth_pct = percent(
        "Expected monthly increase in operating expenses (%)", min_value="-50", max_value="100", placeholder="e.g. 1",
        help_text="For example, to reflect inflation in rent, fuel and salaries.",
    )

    line_item_specs = (
        LineItemSpec("custom_income", "Additional income categories",
                     "Add any other monthly income streams you want listed separately."),
        LineItemSpec("custom_expenses", "Additional expense categories",
                     "Add other monthly costs. Choose “Direct” for costs that grow with sales.",
                     kinds=(("operating", "Operating (fixed)"), ("direct", "Direct (varies with sales)"))),
    )

    extra_lever = ExtraLever(
        label="Monthly growth change (percentage points)",
        help="Added to your monthly revenue growth, e.g. −1 turns 3% growth into 2%.",
        unit="points", conservative=Decimal("-1"), optimistic=Decimal("1"),
        min_value=Decimal("-50"), max_value=Decimal("50"),
    )

    steps = (
        Step("About your business", "Start with the basics. You can change anything later.",
             fields=("project_name", "business_name", "currency"), advanced=("forecast_start",)),
        Step("Monthly income", "Enter what the business earns in a typical month.",
             fields=("monthly_sales",), advanced=("other_income",), advanced_title="Other income and custom categories",
             line_items=("custom_income",)),
        Step("Monthly costs", "Enter what the business spends in a typical month. Leave blank any cost that does not apply.",
             fields=("direct_costs", "salaries", "rent", "utilities"),
             advanced=("marketing", "transport", "software_admin", "other_operating"),
             advanced_title="More expense categories", line_items=("custom_expenses",)),
        Step("Growth and tax", "Optional assumptions for the 12-month forecast.",
             fields=("revenue_growth_pct",), advanced=("expense_growth_pct", "tax_rate_pct")),
        Step("Scenarios", "Test how results change if things go worse or better than expected.", scenarios=True),
    )
