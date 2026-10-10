"""Tests for the shared money and finance helpers."""
from decimal import Decimal as D

from django.test import SimpleTestCase

from financial_models.common.finance import annualised_return, annuity_payment, irr, npv, sign_changes
from financial_models.common.inputs import month_label, serialise
from financial_models.common.money import (
    MissingInputError, format_compact, format_money, format_percent, percentage, safe_divide, to_decimal,
)
from financial_models.common.inputs import dec
from datetime import date


def q(value, places="0.01"):
    return value.quantize(D(places))


class MoneyTests(SimpleTestCase):
    def test_decimal_avoids_float_errors(self):
        self.assertEqual(to_decimal("0.1") + to_decimal("0.2"), D("0.3"))
        self.assertEqual(to_decimal(0.1), D("0.1"))

    def test_blank_is_none_not_zero(self):
        self.assertIsNone(to_decimal(""))
        self.assertIsNone(to_decimal(None))

    def test_invalid_number_raises(self):
        with self.assertRaises(ValueError):
            to_decimal("abc")
        with self.assertRaises(ValueError):
            to_decimal("NaN")

    def test_required_missing_input_raises(self):
        with self.assertRaises(MissingInputError):
            dec({}, "monthly_sales", required=True)
        self.assertIsNone(dec({}, "optional_thing"))

    def test_safe_divide_handles_zero(self):
        self.assertIsNone(safe_divide(D(10), D(0)))
        self.assertIsNone(safe_divide(None, D(1)))
        self.assertEqual(safe_divide(D(10), D(4)), D("2.5"))
        self.assertIsNone(percentage(D(5), D(0)))
        self.assertEqual(percentage(D(1), D(4)), D(25))

    def test_currency_formatting(self):
        self.assertEqual(format_money(D("1234567.891"), "NGN"), "₦1,234,567.89")
        self.assertEqual(format_money(D("-50"), "USD"), "-$50.00")
        self.assertEqual(format_money(D("0.004"), "GBP"), "£0.00")
        self.assertEqual(format_money(D("-0.004"), "GBP"), "£0.00")  # no "-0.00"
        self.assertEqual(format_money(D("1000"), "NGN", style="code"), "NGN 1,000.00")
        self.assertEqual(format_money(None, "NGN"), "Not available")
        self.assertEqual(format_compact(D("1250000"), "NGN"), "₦1.3M")
        self.assertEqual(format_compact(D("-2000"), "USD"), "-$2K")
        self.assertEqual(format_percent(D("12.345")), "12.3%")

    def test_rounding_is_half_up(self):
        self.assertEqual(format_money(D("2.345"), "USD"), "$2.35")

    def test_serialise_round_trip(self):
        data = serialise({"a": D("1.50"), "d": date(2027, 1, 5), "items": [{"amount": D("2")}]})
        self.assertEqual(data, {"a": "1.50", "d": "2027-01-05", "items": [{"amount": "2"}]})

    def test_month_labels(self):
        self.assertEqual(month_label(None, 3), "Month 3")
        self.assertEqual(month_label(date(2026, 11, 20), 3), "Jan 2027")


class FinanceTests(SimpleTestCase):
    def test_npv_known_value(self):
        # -1000 + 500/1.1 + 500/1.21 + 500/1.331 = 243.43
        self.assertEqual(q(npv(D("0.10"), [D(-1000), D(500), D(500), D(500)])), D("243.43"))

    def test_npv_zero_rate_is_simple_sum(self):
        self.assertEqual(npv(D(0), [D(-100), D(60), D(60)]), D(20))

    def test_npv_rejects_rate_at_or_below_minus_100(self):
        with self.assertRaises(ValueError):
            npv(D(-1), [D(-1), D(2)])

    def test_irr_known_values(self):
        self.assertEqual(q(irr([D(-100), D(110)]), "0.0001"), D("0.1000"))
        self.assertEqual(q(irr([D(-1000), D(500), D(500), D(500)]) * 100, "0.01"), D("23.38"))

    def test_irr_at_npv_zero(self):
        rate = irr([D(-1000), D(300), D(400), D(500)])
        self.assertLess(abs(npv(rate, [D(-1000), D(300), D(400), D(500)])), D("0.000001"))

    def test_irr_none_without_sign_change(self):
        self.assertIsNone(irr([D(-100), D(-50)]))
        self.assertIsNone(irr([D(100), D(50)]))

    def test_irr_negative_return(self):
        self.assertEqual(q(irr([D(-100), D(80)]), "0.0001"), D("-0.2000"))

    def test_sign_changes(self):
        self.assertEqual(sign_changes([D(-1), D(0), D(2), D(-3)]), 2)

    def test_annuity_payment(self):
        # Standard result: 100,000 over 12 months at 1% a month = 8,884.88
        self.assertEqual(q(annuity_payment(D(100000), D("0.01"), 12)), D("8884.88"))
        self.assertEqual(annuity_payment(D(1200), D(0), 12), D(100))
        with self.assertRaises(ValueError):
            annuity_payment(D(1), D(0), 0)

    def test_annualised_return(self):
        self.assertEqual(q(annualised_return(D(100), D(121), D(2)), "0.0001"), D("0.1000"))
        self.assertIsNone(annualised_return(D(0), D(121), D(2)))
        self.assertIsNone(annualised_return(D(100), D(-5), D(2)))
        self.assertEqual(annualised_return(D(100), D(0), D(2)), D(-1))
