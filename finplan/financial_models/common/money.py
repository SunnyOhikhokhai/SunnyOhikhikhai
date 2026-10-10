"""
Money and number helpers shared by every FINPLAN model.

Rules followed throughout the calculation engine:

* All monetary values are ``decimal.Decimal`` – never ``float`` – so that
  amounts such as 0.10 + 0.20 add up exactly.
* Full precision is kept during calculations; rounding happens only when a
  value is formatted for display (``format_money`` / ``format_percent``).
* Division goes through ``safe_divide`` which returns ``None`` instead of
  raising ``ZeroDivisionError``. ``None`` means "cannot be calculated", and
  the presentation layer shows an explanation instead of a number.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

ZERO = Decimal("0")
ONE = Decimal("1")
HUNDRED = Decimal("100")
CENT = Decimal("0.01")

CURRENCIES: dict[str, dict[str, str]] = {
    "NGN": {"symbol": "₦", "name": "Nigerian naira"},
    "USD": {"symbol": "$", "name": "US dollar"},
    "GBP": {"symbol": "£", "name": "British pound sterling"},
}
DEFAULT_CURRENCY = "NGN"
CURRENCY_CHOICES = [
    (code, f"{code} · {info['name']} ({info['symbol']})") for code, info in CURRENCIES.items()
]


class MissingInputError(ValueError):
    """Raised when a required input is missing. We never silently use zero."""

    def __init__(self, field: str, label: str | None = None):
        self.field = field
        self.label = label or field.replace("_", " ")
        super().__init__(f"Required input is missing: {self.label}")


def to_decimal(value) -> Decimal | None:
    """Convert user/stored input into a Decimal. Blank values become ``None``."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise ValueError("Booleans are not valid amounts")
    if isinstance(value, float):
        value = repr(value)
    text = str(value).strip().replace(",", "")
    if text == "":
        return None
    try:
        result = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"'{value}' is not a valid number") from exc
    if not result.is_finite():
        raise ValueError(f"'{value}' is not a valid number")
    return result


def or_zero(value: Decimal | None) -> Decimal:
    """Use only for *optional* inputs, where blank genuinely means "none"."""
    return ZERO if value is None else value


def safe_divide(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    """Divide, returning ``None`` when either side is missing or the denominator is zero."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def percentage(part: Decimal | None, whole: Decimal | None) -> Decimal | None:
    """``part ÷ whole × 100``, or ``None`` when ``whole`` is zero or missing."""
    ratio = safe_divide(part, whole)
    return None if ratio is None else ratio * HUNDRED


def pct_to_fraction(pct: Decimal | None) -> Decimal:
    """Turn 12.5 (per cent) into 0.125. Blank optional percentages are zero."""
    return or_zero(pct) / HUNDRED


def round_money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _group(number: Decimal, decimals: int) -> str:
    quant = Decimal(1).scaleb(-decimals)
    rounded = abs(number).quantize(quant, rounding=ROUND_HALF_UP)
    return f"{rounded:,.{decimals}f}"


def format_money(value: Decimal | None, currency: str, style: str = "symbol", decimals: int = 2) -> str:
    """
    Format an amount for display.

    ``style="symbol"`` gives ``₦1,250,000.00``; ``style="code"`` gives
    ``NGN 1,250,000.00`` (used in PDFs, whose built-in fonts lack ₦).
    """
    if value is None:
        return "Not available"
    info = CURRENCIES.get(currency, CURRENCIES[DEFAULT_CURRENCY])
    sign = "-" if value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP) < 0 else ""
    body = _group(value, decimals)
    if style == "code":
        return f"{sign}{currency} {body}"
    return f"{sign}{info['symbol']}{body}"


def format_compact(value: Decimal | None, currency: str, style: str = "symbol") -> str:
    """Short form for chart axes, e.g. ₦1.2M."""
    if value is None:
        return ""
    info = CURRENCIES.get(currency, CURRENCIES[DEFAULT_CURRENCY])
    prefix = info["symbol"] if style == "symbol" else f"{currency} "
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    for threshold, suffix in ((Decimal("1e12"), "T"), (Decimal("1e9"), "B"), (Decimal("1e6"), "M"), (Decimal("1e3"), "K")):
        if magnitude >= threshold:
            short = (magnitude / threshold).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            text = f"{short:f}".rstrip("0").rstrip(".")
            return f"{sign}{prefix}{text}{suffix}"
    return f"{sign}{prefix}{magnitude.quantize(Decimal(1), rounding=ROUND_HALF_UP):,}"


def format_percent(value: Decimal | None, decimals: int = 1) -> str:
    if value is None:
        return "Not available"
    quant = Decimal(1).scaleb(-decimals)
    return f"{value.quantize(quant, rounding=ROUND_HALF_UP):,.{decimals}f}%"


def format_number(value: Decimal | None, decimals: int = 0) -> str:
    if value is None:
        return "Not available"
    quant = Decimal(1).scaleb(-decimals)
    return f"{value.quantize(quant, rounding=ROUND_HALF_UP):,.{decimals}f}"


def currency_symbol(currency: str) -> str:
    return CURRENCIES.get(currency, CURRENCIES[DEFAULT_CURRENCY])["symbol"]
