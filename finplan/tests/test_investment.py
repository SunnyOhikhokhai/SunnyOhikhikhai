"""Investment model: ROI, annualised return, NPV and IRR are distinct."""
from decimal import Decimal as D

from django.test import SimpleTestCase

from financial_models.common.report import Formatter
from financial_models.common.scenarios import ScenarioAdjustment
from financial_models.investment.calculations import InvestmentInputs, calculate
from financial_models.investment.forms import InvestmentForm
from financial_models.investment.report import build_report

BASE = {
    "project_name": "Fund", "investment_name": "Fund A", "currency": "NGN", "investment_type": "business",
    "initial_investment": "1000", "duration_years": "3", "annual_income": "500", "discount_rate_pct": "10",
}


def q(value, places="0.01"):
    return value.quantize(D(places))


class InvestmentCalculationTests(SimpleTestCase):
    def test_known_case(self):
        r = calculate(InvestmentInputs.from_dict(BASE))
        self.assertEqual(r.cash_flows, [D(-1000), D(500), D(500), D(500)])
        self.assertEqual(r.total_capital, D(1000))
        self.assertEqual(r.total_income, D(1500))
        self.assertEqual(r.net_profit, D(500))
        self.assertEqual(r.roi_pct, D(50))
        self.assertEqual(q(r.npv), D("243.43"))
        self.assertEqual(q(r.irr_pct), D("23.38"))
        self.assertEqual(q(r.annualised_return_pct), D("14.47"))  # 1.5^(1/3) − 1
        self.assertEqual(r.payback_year, 2)

    def test_roi_annualised_and_irr_differ(self):
        r = calculate(InvestmentInputs.from_dict(BASE))
        self.assertNotEqual(q(r.roi_pct), q(r.irr_pct))
        self.assertNotEqual(q(r.annualised_return_pct), q(r.irr_pct))

    def test_single_period_exit(self):
        r = calculate(InvestmentInputs.from_dict({**BASE, "initial_investment": "100", "duration_years": "1",
                                                  "annual_income": "0", "exit_value": "110"}))
        self.assertEqual(q(r.irr_pct), D("10.00"))
        self.assertEqual(r.roi_pct, D(10))
        self.assertEqual(q(r.annualised_return_pct), D("10.00"))

    def test_tax_and_expenses(self):
        r = calculate(InvestmentInputs.from_dict({**BASE, "annual_income": "1000", "annual_expenses": "200",
                                                  "annual_financing_costs": "100", "tax_rate_pct": "30", "duration_years": "1"}))
        self.assertEqual(r.years[1].tax, D(210))  # (1000 − 200 − 100) × 30%
        self.assertEqual(r.cash_flows[1], D(490))
        self.assertEqual(r.total_expenses, D(510))

    def test_contributions_disable_annualised_return(self):
        r = calculate(InvestmentInputs.from_dict({**BASE, "additional_contribution": "100"}))
        self.assertEqual(r.total_capital, D(1300))
        self.assertIsNone(r.annualised_return_pct)
        self.assertIn("IRR", r.annualised_note)
        self.assertEqual(r.net_profit, D(200))

    def test_no_irr_when_never_positive(self):
        r = calculate(InvestmentInputs.from_dict({**BASE, "annual_income": "0"}))
        self.assertIsNone(r.irr_pct)
        self.assertEqual(r.roi_pct, D(-100))
        self.assertEqual(r.annualised_return_pct, D(-100))
        self.assertIsNone(r.payback_year)

    def test_no_discount_rate_no_npv(self):
        data = {k: v for k, v in BASE.items() if k != "discount_rate_pct"}
        self.assertIsNone(calculate(InvestmentInputs.from_dict(data)).npv)

    def test_income_growth(self):
        r = calculate(InvestmentInputs.from_dict({**BASE, "income_growth_pct": "10"}))
        self.assertEqual(r.years[2].income, D(550))
        self.assertEqual(r.years[3].income, D(605))

    def test_scenario_exit_change(self):
        inputs = InvestmentInputs.from_dict({**BASE, "exit_value": "1000"})
        worst = inputs.adjusted(ScenarioAdjustment(D(-20), D(10), D(-25)))
        self.assertEqual(worst.exit_value, D(750))
        self.assertEqual(worst.annual_income, D(400))

    def test_report_labels(self):
        report = build_report(BASE, Formatter("GBP"))
        self.assertEqual(report.scenario_table.columns, ["Measure", "Worst case", "Expected case", "Best case"])
        self.assertEqual(report.headline[1].value, "£500.00")


class InvestmentFormTests(SimpleTestCase):
    def test_duration_bounds(self):
        self.assertIn("duration_years", InvestmentForm({**BASE, "duration_years": "0"}).errors)
        self.assertIn("duration_years", InvestmentForm({**BASE, "duration_years": "2.5"}).errors)

    def test_valid(self):
        self.assertTrue(InvestmentForm(BASE).is_valid())
