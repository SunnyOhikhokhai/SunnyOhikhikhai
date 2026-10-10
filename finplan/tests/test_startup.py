"""Startup model: runway, break-even, funding and loans."""
from decimal import Decimal as D

from django.test import SimpleTestCase

from financial_models.common.report import Formatter
from financial_models.common.scenarios import ScenarioAdjustment
from financial_models.startup.calculations import StartupInputs, calculate
from financial_models.startup.forms import StartupForm
from financial_models.startup.report import build_report

BASE = {
    "project_name": "Launch", "startup_name": "QuickWash", "currency": "NGN",
    "initial_capital": "1000000", "equipment_setup": "300000", "registration_fees": "100000",
    "customers_month_1": "10", "revenue_per_customer": "10000", "monthly_operating_expenses": "150000",
    "forecast_months": "12",
}


def q(value, places="0.01"):
    return value.quantize(D(places))


class StartupCalculationTests(SimpleTestCase):
    def test_launch_costs_and_cash_after_launch(self):
        r = calculate(StartupInputs.from_dict(BASE))
        self.assertEqual(r.total_launch_costs, D(400000))
        self.assertEqual(r.cash_after_launch, D(600000))
        self.assertEqual(r.months[0].revenue, D(100000))
        self.assertEqual(r.months[0].operating_profit, D(-50000))
        self.assertEqual(r.months[0].burn, D(50000))

    def test_runway_beyond_horizon_when_cash_never_negative(self):
        r = calculate(StartupInputs.from_dict(BASE))
        self.assertEqual(r.months[-1].closing_cash, D(0))  # exactly zero after 12 months
        self.assertIsNone(r.runway_months)
        self.assertEqual(r.additional_funding_needed, D(0))

    def test_runway_from_month_by_month_forecast(self):
        r = calculate(StartupInputs.from_dict({**BASE, "forecast_months": "24"}))
        self.assertEqual(r.runway_months, 12)
        self.assertEqual(r.runs_out_label, "Month 13")
        self.assertEqual(r.additional_funding_needed, D(600000))
        self.assertEqual(r.total_funding_required, D(1600000))  # 400k launch + 24 × 50k losses

    def test_runway_not_simple_division_when_growing(self):
        # With 10% customer growth losses shrink, so cash lasts longer than 600k ÷ 50k = 12 months.
        r = calculate(StartupInputs.from_dict({**BASE, "customer_growth_pct": "10", "forecast_months": "24"}))
        self.assertIsNone(r.runway_months)
        self.assertEqual(r.break_even_month.index, 6)  # 1.1^5 = 1.61 ≥ 1.5

    def test_cash_runs_out_at_launch(self):
        r = calculate(StartupInputs.from_dict({**BASE, "initial_capital": "100000"}))
        self.assertEqual(r.runway_months, 0)
        self.assertEqual(r.runs_out_label, "At launch")

    def test_break_even_customers(self):
        r = calculate(StartupInputs.from_dict({**BASE, "direct_cost_pct": "25"}))
        self.assertEqual(r.break_even_customers, D(20))  # 150,000 ÷ (10,000 × 0.75)

    def test_direct_costs_of_100_percent_never_break_even(self):
        r = calculate(StartupInputs.from_dict({**BASE, "direct_cost_pct": "100"}))
        self.assertIsNone(r.break_even_customers)
        self.assertIsNone(r.break_even_month)

    def test_interest_free_loan(self):
        r = calculate(StartupInputs.from_dict({**BASE, "loan_amount": "120000", "loan_interest_pct": "0", "loan_term_months": "12"}))
        self.assertEqual(r.monthly_loan_payment, D(10000))
        self.assertEqual(r.months[0].loan_principal, D(10000))
        self.assertEqual(r.months[0].loan_interest, D(0))
        self.assertEqual(r.cash_after_launch, D(720000))
        self.assertEqual(q(r.months[-1].closing_cash), D(0))  # 720k − 12 × (50k + 10k)

    def test_loan_with_interest(self):
        r = calculate(StartupInputs.from_dict({**BASE, "loan_amount": "100000", "loan_interest_pct": "12", "loan_term_months": "12"}))
        self.assertEqual(q(r.monthly_loan_payment), D("8884.88"))
        self.assertEqual(q(r.months[0].loan_interest), D("1000.00"))
        repaid = sum(m.loan_principal for m in r.months)
        self.assertEqual(q(repaid), D("100000.00"))

    def test_planned_funding_month(self):
        r = calculate(StartupInputs.from_dict({**BASE, "planned_funding": "500000", "planned_funding_month": "3"}))
        self.assertEqual(r.months[2].funding_in, D(500000))
        self.assertEqual(r.months[2].closing_cash, D(600000) - 3 * D(50000) + D(500000))
        self.assertEqual(r.total_funding_available, D(1500000))

    def test_scenario_changes_growth(self):
        inputs = StartupInputs.from_dict({**BASE, "customer_growth_pct": "5"})
        adjusted = inputs.adjusted(ScenarioAdjustment(D(0), D(0), D(-2)))
        self.assertEqual(adjusted.customer_growth_pct, D(3))

    def test_report(self):
        report = build_report({**BASE, "forecast_months": "24"}, Formatter("USD"))
        self.assertEqual(report.headline[1].value, "12 months")
        self.assertEqual(report.headline[3].value, "$600,000.00")


class StartupFormTests(SimpleTestCase):
    def test_loan_requires_rate_and_term(self):
        form = StartupForm({**BASE, "loan_amount": "50000"})
        self.assertFalse(form.is_valid())
        self.assertIn("loan_interest_pct", form.errors)
        self.assertIn("loan_term_months", form.errors)

    def test_funding_requires_month(self):
        form = StartupForm({**BASE, "planned_funding": "50000"})
        self.assertFalse(form.is_valid())
        self.assertIn("planned_funding_month", form.errors)

    def test_funding_month_inside_forecast(self):
        form = StartupForm({**BASE, "planned_funding": "50000", "planned_funding_month": "20"})
        self.assertFalse(form.is_valid())

    def test_valid(self):
        self.assertTrue(StartupForm(BASE).is_valid())
