"""Real estate model: costs, profit, yields, subdivision and timeline."""
from decimal import Decimal as D

from django.test import SimpleTestCase

from financial_models.common.report import Formatter
from financial_models.common.scenarios import ScenarioAdjustment
from financial_models.real_estate.calculations import RealEstateInputs, calculate
from financial_models.real_estate.forms import RealEstateForm
from financial_models.real_estate.report import build_report

SALES = {
    "project_name": "Palm Court", "currency": "NGN", "project_type": "residential", "income_type": "sales",
    "duration_months": "18", "land_cost": "50000000", "legal_docs": "5000000", "survey_design": "3000000",
    "construction": "100000000", "professional_fees": "7000000", "contingency_pct": "10",
    "marketing_sales": "4000000", "financing_costs": "6000000", "units": "20", "sale_price_per_unit": "12000000",
}
RENTAL = {
    "project_name": "Flats", "currency": "NGN", "project_type": "rental", "income_type": "rental",
    "duration_months": "6", "land_cost": "20000000", "construction": "30000000",
    "annual_rent": "6000000", "vacancy_pct": "10", "annual_rental_expenses": "1000000", "rental_years": "5",
}


def q(value, places="0.01"):
    return value.quantize(D(places))


class RealEstateCalculationTests(SimpleTestCase):
    def test_sales_project(self):
        r = calculate(RealEstateInputs.from_dict(SALES))
        self.assertEqual(r.acquisition_cost, D(55000000))
        self.assertEqual(r.development_base, D(110000000))
        self.assertEqual(r.contingency, D(11000000))
        self.assertEqual(r.total_development_cost, D(125000000))
        self.assertEqual(r.total_project_cost, D(186000000))
        self.assertEqual(r.sales_revenue, D(240000000))
        self.assertEqual(r.gross_profit, D(60000000))
        self.assertEqual(r.net_profit, D(54000000))
        self.assertEqual(r.profit_margin_pct, D("22.5"))
        self.assertEqual(q(r.roi_pct), D("29.03"))
        self.assertEqual(r.break_even_price, D(9300000))

    def test_timeline_adds_up(self):
        r = calculate(RealEstateInputs.from_dict(SALES))
        self.assertEqual(len(r.timeline), 18)
        self.assertEqual(q(sum(p.costs for p in r.timeline)), D("186000000.00"))
        self.assertEqual(q(sum(p.income for p in r.timeline)), D("240000000.00"))
        self.assertEqual(q(r.timeline[-1].cumulative), D("54000000.00"))
        self.assertEqual(r.sales_start_month, 10)  # default: halfway
        self.assertEqual(r.timeline[8].income, D(0))
        self.assertGreater(r.peak_cash_need, 0)

    def test_rental_project(self):
        r = calculate(RealEstateInputs.from_dict(RENTAL))
        self.assertEqual(r.total_project_cost, D(50000000))
        self.assertEqual(r.gross_rental_income, D(30000000))
        self.assertEqual(r.effective_rental_income, D(27000000))
        self.assertEqual(r.rental_operating_costs, D(5000000))
        self.assertEqual(r.net_profit, D(-28000000))
        self.assertEqual(r.gross_yield_pct, D(12))
        self.assertEqual(r.net_yield_pct, D("8.8"))
        self.assertIsNone(r.break_even_price)
        self.assertEqual(len(r.timeline), 6 + 60)

    def test_subdivision_net_saleable_area(self):
        data = {**SALES, "project_type": "land_subdivision", "gross_land_area": "10000",
                "roads_pct": "20", "drainage_pct": "5", "public_space_pct": "5", "plot_size": "500"}
        r = calculate(RealEstateInputs.from_dict(data))
        self.assertEqual(r.subdivision.unsaleable_pct, D(30))
        self.assertEqual(r.subdivision.net_saleable_area, D(7000))
        self.assertEqual(r.subdivision.max_plots, 14)
        report = build_report(data, Formatter("NGN"))
        self.assertTrue(any("only fits about 14 plots" in w for w in report.warnings))

    def test_zero_cost_safe(self):
        data = {**RENTAL, "land_cost": "0", "construction": "0"}
        r = calculate(RealEstateInputs.from_dict(data))
        self.assertIsNone(r.roi_pct)
        self.assertIsNone(r.gross_yield_pct)

    def test_delay_scenario(self):
        inputs = RealEstateInputs.from_dict({**SALES, "sales_start_month": "12"})
        adjusted = inputs.adjusted(ScenarioAdjustment(D(-10), D(10), D(6)))
        self.assertEqual(adjusted.duration_months, 24)
        self.assertEqual(adjusted.sales_start_month, 18)
        self.assertEqual(adjusted.sale_price_per_unit, D(10800000))
        self.assertEqual(adjusted.land_cost, D(50000000))  # land price is not scaled
        self.assertEqual(adjusted.construction, D(110000000))

    def test_long_timeline_is_grouped(self):
        data = {**RENTAL, "rental_years": "10"}
        report = build_report(data, Formatter("NGN"))
        timeline = report.tables[1]
        self.assertTrue(timeline.rows[0][0].startswith("Year") or timeline.rows[0][0].startswith("Quarter"))


class RealEstateFormTests(SimpleTestCase):
    def test_sales_requires_units_and_price(self):
        data = {k: v for k, v in SALES.items() if k not in ("units", "sale_price_per_unit")}
        form = RealEstateForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("units", form.errors)
        self.assertIn("sale_price_per_unit", form.errors)

    def test_rental_requires_rent(self):
        data = {k: v for k, v in RENTAL.items() if k != "annual_rent"}
        self.assertIn("annual_rent", RealEstateForm(data).errors)

    def test_set_asides_must_be_below_100(self):
        form = RealEstateForm({**SALES, "project_type": "land_subdivision", "roads_pct": "60", "public_space_pct": "40"})
        self.assertFalse(form.is_valid())

    def test_sales_start_after_end_rejected(self):
        form = RealEstateForm({**SALES, "sales_start_month": "30"})
        self.assertIn("sales_start_month", form.errors)

    def test_valid_forms(self):
        self.assertTrue(RealEstateForm(SALES).is_valid())
        self.assertTrue(RealEstateForm(RENTAL).is_valid())
