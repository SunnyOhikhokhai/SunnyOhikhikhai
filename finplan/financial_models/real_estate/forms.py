"""Input form for the Real Estate Financial Model."""
from decimal import Decimal

from django import forms

from ..common.forms import LineItemSpec, ModelInputForm, Step, money, percent, quantity, whole
from ..common.scenarios import ExtraLever
from .calculations import INCOME_TYPES, PROJECT_TYPES, SUBDIVISION_FIELDS


class RealEstateForm(ModelInputForm):
    location = forms.CharField(label="Project location", max_length=160, required=False,
                               help_text="For example “Ibeju-Lekki, Lagos”.")
    project_type = forms.ChoiceField(label="Project type", choices=PROJECT_TYPES, initial="residential")
    income_type = forms.ChoiceField(
        label="How will the project earn money?", choices=INCOME_TYPES, initial="sales",
        help_text="Choose sales, rental income, or both.",
    )
    duration_months = whole("Expected project duration (months)", required=True, min_value=1, max_value=240,
                            placeholder="e.g. 18",
                            help_text="From buying the land to finishing construction and sales.")
    land_cost = money("Land acquisition cost", required=True, placeholder="e.g. 60000000",
                      help_text="Purchase price of the land or property.")
    legal_docs = money("Legal and documentation costs", help_text="Survey plan, deed, Governor's consent, legal fees.")
    survey_design = money("Survey, design and planning costs", help_text="Architectural drawings, approvals and permits.")
    construction = money("Construction or infrastructure costs", required=True, placeholder="e.g. 150000000",
                         help_text="Building works, or roads, drainage and power for land projects. Enter 0 if none.")
    professional_fees = money("Professional fees", help_text="Engineers, quantity surveyors, project managers.")
    marketing_sales = money("Marketing and sales costs", help_text="Adverts, agents' commission, show units.")
    contingency_pct = percent("Contingency allowance (%)", placeholder="e.g. 10",
                              help_text="Extra buffer for unexpected costs, as a share of design, construction, "
                                        "professional and other costs. 5–15% is common.")
    financing_costs = money("Financing costs", help_text="Total interest and loan fees over the project, if borrowing.")
    units = whole("Number of plots or units for sale", min_value=1, max_value=100000, placeholder="e.g. 20")
    sale_price_per_unit = money("Expected sale price per plot or unit", placeholder="e.g. 25000000")
    sales_start_month = whole("Month sales begin", min_value=1, max_value=240,
                              help_text="Leave blank to assume sales start halfway through the project.")
    annual_rent = money("Expected annual rental income (all units)", help_text="Total rent per year when fully let.")
    vacancy_pct = percent("Vacancy allowance (%)", placeholder="e.g. 10",
                          help_text="Share of the year units may be empty or rent unpaid.")
    annual_rental_expenses = money("Annual rental operating expenses",
                                   help_text="Maintenance, facility management, insurance and service charges.")
    rental_years = whole("Rental period to include (years)", min_value=1, max_value=30, placeholder="e.g. 5",
                         help_text="How many years of rent to include in the projection.")
    gross_land_area = quantity("Gross land area (square metres)", placeholder="e.g. 20000")
    roads_pct = percent("Roads (% of land)", help_text="Land used for internal roads.")
    drainage_pct = percent("Drainage (% of land)")
    public_space_pct = percent("Public and green spaces (% of land)")
    other_unsaleable_pct = percent("Other unsaleable land (% of land)", help_text="Setbacks, utilities, community facilities.")
    plot_size = quantity("Typical plot size (square metres)", placeholder="e.g. 500")

    line_item_specs = (
        LineItemSpec("other_costs", "Other project costs",
                     "Add any other costs, e.g. fencing, site security or utility connections."),
    )

    extra_lever = ExtraLever(
        label="Project delay (months)",
        help="Months added to (or removed from) the project duration. Sales timing moves with it.",
        unit="months", conservative=Decimal("6"), optimistic=Decimal("0"),
        min_value=Decimal("-60"), max_value=Decimal("120"),
    )

    steps = (
        Step("About the project", "Describe the property project.",
             fields=("project_name", "currency", "project_type", "income_type", "duration_months"),
             advanced=("location",)),
        Step("Land and acquisition", "What it costs to secure the land or property.",
             fields=("land_cost", "legal_docs")),
        Step("Land subdivision details", "Not all land can be sold – roads, drainage and public spaces take up part of it.",
             fields=("gross_land_area", "plot_size"), advanced=("roads_pct", "drainage_pct", "public_space_pct", "other_unsaleable_pct"),
             advanced_title="Land set aside (not saleable)",
             show_if=("project_type", ("land_subdivision",))),
        Step("Development costs", "Costs to design and build. Leave blank any that do not apply.",
             fields=("construction", "survey_design", "professional_fees", "contingency_pct"),
             advanced=("marketing_sales", "financing_costs"), advanced_title="Marketing and financing",
             line_items=("other_costs",)),
        Step("Sales income", "What you expect to earn from selling plots or units.",
             fields=("units", "sale_price_per_unit"), advanced=("sales_start_month",),
             show_if=("income_type", ("sales", "both"))),
        Step("Rental income", "What you expect to earn from renting out the property.",
             fields=("annual_rent", "rental_years", "vacancy_pct", "annual_rental_expenses"),
             show_if=("income_type", ("rental", "both"))),
        Step("Scenarios", "Test lower prices, higher costs or delays.", scenarios=True),
    )

    def clean(self):
        cleaned = super().clean()
        income_type = cleaned.get("income_type")
        if income_type in ("sales", "both"):
            if not cleaned.get("units"):
                self.add_error("units", "Enter how many plots or units you plan to sell.")
            if cleaned.get("sale_price_per_unit") is None:
                self.add_error("sale_price_per_unit", "Enter the expected sale price per plot or unit.")
        if income_type in ("rental", "both"):
            if cleaned.get("annual_rent") is None:
                self.add_error("annual_rent", "Enter the expected annual rental income.")
            if not cleaned.get("rental_years"):
                self.add_error("rental_years", "Enter how many years of rent to include.")
        duration = cleaned.get("duration_months")
        start = cleaned.get("sales_start_month")
        if duration and start and start > duration:
            self.add_error("sales_start_month", "Sales cannot start after the project ends.")
        if cleaned.get("project_type") == "land_subdivision":
            total = sum((cleaned.get(f) or Decimal("0")) for f in SUBDIVISION_FIELDS)
            if total >= 100:
                self.add_error("roads_pct", "Roads, drainage, public spaces and other set-asides must be less than 100% of the land.")
        return cleaned
