"""
Standard finance formulas used by the models.

Every function documents its formula and returns ``None`` (rather than
raising) when the inputs do not support a meaningful answer.
"""
from __future__ import annotations

from decimal import Decimal

from .money import ONE, ZERO


def grow(base: Decimal, rate: Decimal, periods: int) -> Decimal:
    """Compound growth: ``base × (1 + rate) ^ periods`` (rate as a fraction)."""
    return base * (ONE + rate) ** periods


def npv(rate: Decimal, cashflows: list[Decimal]) -> Decimal:
    """
    Net present value.

        NPV = Σ  CFₜ ÷ (1 + r)ᵗ   for t = 0 … n

    ``cashflows[0]`` happens today (t = 0) and is not discounted.
    ``rate`` is a fraction per period (10% → 0.10) and must be above -100%.
    """
    factor = ONE + rate
    if factor <= 0:
        raise ValueError("Discount rate must be greater than -100%")
    total = ZERO
    for period, amount in enumerate(cashflows):
        total += amount / factor**period
    return total


def sign_changes(cashflows: list[Decimal]) -> int:
    """Count sign changes, ignoring zeros. More than one can mean several IRRs."""
    signs = [1 if cf > 0 else -1 for cf in cashflows if cf != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if a != b)


def irr(cashflows: list[Decimal], low: Decimal = Decimal("-0.9999"), high: Decimal = Decimal("10"),
        tolerance: Decimal = Decimal("1e-12"), max_iterations: int = 500) -> Decimal | None:
    """
    Internal rate of return: the rate ``r`` at which ``NPV(r) = 0``.

    Found by bisection between ``low`` and ``high`` (−99.99% … +1,000% per
    period). Returns ``None`` when the cash flows never change sign (no IRR
    exists) or when NPV does not cross zero inside the search range.
    """
    if not any(cf > 0 for cf in cashflows) or not any(cf < 0 for cf in cashflows):
        return None
    npv_low = npv(low, cashflows)
    npv_high = npv(high, cashflows)
    if npv_low == 0:
        return low
    if npv_high == 0:
        return high
    if (npv_low > 0) == (npv_high > 0):
        return None
    for _ in range(max_iterations):
        mid = (low + high) / 2
        npv_mid = npv(mid, cashflows)
        if abs(npv_mid) < tolerance or (high - low) / 2 < tolerance:
            return mid
        if (npv_mid > 0) == (npv_low > 0):
            low, npv_low = mid, npv_mid
        else:
            high = mid
    return (low + high) / 2


def annuity_payment(principal: Decimal, periodic_rate: Decimal, periods: int) -> Decimal:
    """
    Level repayment for an amortising loan.

        Payment = P × r ÷ (1 − (1 + r)^−n)     (or P ÷ n when r = 0)
    """
    if periods <= 0:
        raise ValueError("Loan term must be at least one period")
    if periodic_rate == 0:
        return principal / periods
    return principal * periodic_rate / (ONE - (ONE + periodic_rate) ** -periods)


def annualised_return(start_value: Decimal, end_value: Decimal, years: Decimal) -> Decimal | None:
    """
    Compound annual growth rate (as a fraction):

        (End value ÷ Start value) ^ (1 ÷ years) − 1

    ``None`` when the start value or the period is not positive, or the end
    value is negative (a fractional power of a negative number is undefined).
    """
    if start_value <= 0 or years <= 0 or end_value < 0:
        return None
    if end_value == 0:
        return Decimal("-1")
    return (end_value / start_value) ** (ONE / years) - ONE
