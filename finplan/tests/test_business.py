"""Business model: hand-checked known cases."""
from decimal import Decimal as D

from django.test import SimpleTestCase

from financial_models.business.calculations import BusinessInputs, calculate
from financial_models.business.forms import BusinessForm
from financial_models.business.report import build_report
from financial_models.common.money import MissingInputError
from financial_models.common.report import Formatter
from financial_models.common.scenarios import ScenarioAdjustment

BASE = {
    "project_name": "Bakery", "business_name": "Ada's Bakery", "currency": "NGN",
    "monthly_sales": "1000000", "other_income": "100000", "direct_costs": "440000",
    "salaries": "300000", "rent": "100000", "utilities": "50000", "tax_rate_pct": "30",
}


def q(value, places="0.01"):
    return value.quantize(D(places))


class BusinessCalculationTests(SimpleTestCase):
    def setUp(self):
        self.result = calculate(BusinessInputs.from_dict(BASE))

    def test_profit_and_loss(self):
        r = self.result
        self.assertEqual(r.total_revenue, D(1100000))
        self.assertEqual(r.total_direct_costs, D(440000))
        self.assertEqual(r.gross_profit, D(660000))
        self.assertEqual(r.gross_margin_pct, D(60))
        self.assertEqual(r.total_operating_expenses, D(450000))
        self.assertEqual(r.operating_profit, D(210000))
        self.assertEqual(r.profit_before_tax, D(210000))
        self.assertEqual(r.tax, D(63000))
        self.assertEqual(r.profit_after_tax, D(147000))
        self.assertEqual(q(r.net_margin_pct), D("13.36"))

    def test_break_even(self):
        r = self.result
        self.assertEqual(r.contribution_margin_ratio, D("0.6"))
        self.assertEqual(r.break_even_revenue, D(750000))  # 450,000 ÷ 0.6
        self.assertEqual(q(r.margin_of_safety_pct), D("31.82"))

    def test_flat_forecast(self):
        r = self.result
        self.assertEqual(len(r.forecast), 12)
        self.assertEqual(r.annual_revenue, D(13200000))
        self.assertEqual(r.annual_profit_before_tax, D(2520000))
        self.assertEqual(r.annual_tax, D(756000))
        self.assertEqual(r.forecast[-1].cumulative_profit, D(2520000))

    def test_growth_forecast(self):
        r = calculate(BusinessInputs.from_dict({**BASE, "revenue_growth_pct": "10", "expense_growth_pct": "5"}))
        self.assertEqual(r.forecast[1].revenue, D(1210000))
        self.assertEqual(r.forecast[1].direct_costs, D(484000))  # direct costs stay 40% of revenue
        self.assertEqual(r.forecast[1].operating_expenses, D("472500"))

    def test_no_tax_rate_means_tax_not_included(self):
        data = {k: v for k, v in BASE.items() if k != "tax_rate_pct"}
        r = calculate(BusinessInputs.from_dict(data))
        self.assertIsNone(r.tax)
        self.assertEqual(r.profit_after_tax, D(210000))

    def test_no_tax_on_losses(self):
        r = calculate(BusinessInputs.from_dict({**BASE, "monthly_sales": "500000"}))
        self.assertLess(r.profit_before_tax, 0)
        self.assertEqual(r.tax, D(0))

    def test_zero_revenue_is_safe(self):
        r = calculate(BusinessInputs.from_dict({**BASE, "monthly_sales": "0", "other_income": ""}))
        self.assertIsNone(r.gross_margin_pct)
        self.assertIsNone(r.net_margin_pct)
        self.assertIsNone(r.break_even_revenue)
        self.assertIn("revenue above zero", r.break_even_note)

    def test_direct_costs_above_revenue_cannot_break_even(self):
        r = calculate(BusinessInputs.from_dict({**BASE, "direct_costs": "1200000"}))
        self.assertIsNone(r.break_even_revenue)
        self.assertIn("cannot be reached", r.break_even_note)

    def test_custom_lines(self):
        data = {**BASE, "custom_income": [{"name": "Catering", "amount": "50000"}],
                "custom_expenses": [{"name": "Flour", "amount": "10000", "kind": "direct"},
                                    {"name": "Security", "amount": "20000", "kind": "operating"}]}
        r = calculate(BusinessInputs.from_dict(data))
        self.assertEqual(r.total_revenue, D(1150000))
        self.assertEqual(r.total_direct_costs, D(450000))
        self.assertEqual(r.total_operating_expenses, D(470000))

    def test_missing_required_input_is_not_zero(self):
        with self.assertRaises(MissingInputError):
            BusinessInputs.from_dict({k: v for k, v in BASE.items() if k != "monthly_sales"})

    def test_scenario_adjustment(self):
        inputs = BusinessInputs.from_dict(BASE)
        r = calculate(inputs.adjusted(ScenarioAdjustment(D(-10), D(10), D(0))))
        self.assertEqual(r.total_revenue, D(990000))
        self.assertEqual(r.total_direct_costs, D(484000))
        self.assertEqual(r.total_operating_expenses, D(495000))

    def test_report_builds_with_scenarios(self):
        report = build_report({**BASE, "scn_conservative_revenue_pct": "-15"}, Formatter("NGN"))
        self.assertEqual(report.headline[1].value, "₦147,000.00")
        self.assertEqual(report.scenario_table.columns, ["Measure", "Conservative", "Expected", "Optimistic"])


class BusinessFormTests(SimpleTestCase):
    def test_valid_form_and_storable(self):
        form = BusinessForm({**BASE, "custom_expenses_name": ["Flour"], "custom_expenses_amount": ["1000"],
                             "custom_expenses_kind": ["direct"]})
        self.assertTrue(form.is_valid(), form.errors)
        stored = form.storable()
        self.assertEqual(stored["monthly_sales"], "1000000")
        self.assertEqual(stored["custom_expenses"], [{"name": "Flour", "amount": "1000", "kind": "direct"}])
        # Scenario fields left blank are stored as a neutral 0% adjustment.
        self.assertEqual(stored["scn_conservative_revenue_pct"], "0")

    def test_required_fields(self):
        form = BusinessForm({"project_name": "x", "business_name": "y", "currency": "NGN"})
        self.assertFalse(form.is_valid())
        self.assertIn("monthly_sales", form.errors)
        self.assertIn("direct_costs", form.errors)

    def test_negative_amount_rejected(self):
        form = BusinessForm({**BASE, "rent": "-5"})
        self.assertFalse(form.is_valid())
        self.assertIn("rent", form.errors)

    def test_invalid_currency_rejected(self):
        form = BusinessForm({**BASE, "currency": "EUR"})
        self.assertFalse(form.is_valid())

    def test_bad_line_item(self):
        form = BusinessForm({**BASE, "custom_income_name": ["", "Tips"], "custom_income_amount": ["500", "abc"]})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.line_item_errors["custom_income"]), 2)

    def test_percentage_range(self):
        form = BusinessForm({**BASE, "tax_rate_pct": "150"})
        self.assertFalse(form.is_valid())
        self.assertIn("tax_rate_pct", form.errors)
