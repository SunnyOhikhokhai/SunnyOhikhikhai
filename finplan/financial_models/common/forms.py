"""
Shared building blocks for the four model input forms.

Each model form subclasses ``ModelInputForm`` and declares:

* its fields (using the ``money``/``percent``/``whole`` helpers),
* ``steps`` – how the form is split into short guided steps, with
  advanced/optional fields tucked behind "More options" (progressive
  disclosure),
* ``line_item_specs`` – user-defined rows such as custom expenses,
* ``extra_lever`` – the model-specific scenario setting.

All validation happens on the server; the browser-side JavaScript only
improves the experience (step navigation, adding rows).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django import forms

from .inputs import serialise
from .money import CURRENCY_CHOICES, DEFAULT_CURRENCY, to_decimal
from .scenarios import DEFAULT_COST, DEFAULT_REVENUE, ExtraLever, field_name

MAX_AMOUNT = Decimal("999999999999999.99")
MAX_LINE_ITEMS = 25


def money(label: str, required: bool = False, help_text: str = "", placeholder: str = "") -> forms.DecimalField:
    return forms.DecimalField(
        label=label,
        required=required,
        help_text=help_text,
        min_value=Decimal("0"),
        max_value=MAX_AMOUNT,
        max_digits=17,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "step": "0.01", "min": "0", "inputmode": "decimal", "data-money": "1",
            "placeholder": placeholder,
        }),
    )


def percent(label: str, required: bool = False, help_text: str = "", min_value: str = "0",
            max_value: str = "100", placeholder: str = "") -> forms.DecimalField:
    return forms.DecimalField(
        label=label,
        required=required,
        help_text=help_text,
        min_value=Decimal(min_value),
        max_value=Decimal(max_value),
        max_digits=7,
        decimal_places=3,
        widget=forms.NumberInput(attrs={
            "step": "0.001", "min": min_value, "max": max_value, "inputmode": "decimal",
            "data-percent": "1", "placeholder": placeholder,
        }),
    )


def whole(label: str, required: bool = False, help_text: str = "", min_value: int = 0,
          max_value: int = 1000, placeholder: str = "") -> forms.IntegerField:
    return forms.IntegerField(
        label=label,
        required=required,
        help_text=help_text,
        min_value=min_value,
        max_value=max_value,
        widget=forms.NumberInput(attrs={
            "step": "1", "min": str(min_value), "max": str(max_value), "inputmode": "numeric",
            "placeholder": placeholder,
        }),
    )


def quantity(label: str, required: bool = False, help_text: str = "", placeholder: str = "") -> forms.DecimalField:
    """A non-money number that may have decimals (e.g. customers, square metres)."""
    return forms.DecimalField(
        label=label,
        required=required,
        help_text=help_text,
        min_value=Decimal("0"),
        max_value=Decimal("999999999999"),
        max_digits=16,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "any", "min": "0", "inputmode": "decimal", "placeholder": placeholder}),
    )


@dataclass(frozen=True)
class LineItemSpec:
    """A list of user-defined rows, e.g. custom expense categories."""

    key: str
    title: str
    help: str
    name_label: str = "Description"
    amount_label: str = "Amount"
    kinds: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Step:
    title: str
    intro: str = ""
    fields: tuple[str, ...] = ()
    advanced: tuple[str, ...] = ()
    advanced_title: str = "More options"
    line_items: tuple[str, ...] = ()
    scenarios: bool = False
    # Show this step only when another field has one of these values.
    show_if: tuple[str, tuple[str, ...]] | None = None


@dataclass
class BoundStep:
    number: int
    title: str
    intro: str
    fields: list
    advanced: list
    advanced_title: str
    line_items: list = field(default_factory=list)
    scenario_rows: list = field(default_factory=list)
    show_if_field: str = ""
    show_if_values: str = ""
    has_errors: bool = False


def collect_line_item_rows(data, spec: LineItemSpec) -> list[dict]:
    """Read raw submitted rows (unvalidated) so they can be redisplayed."""
    getlist = data.getlist if hasattr(data, "getlist") else (lambda k: data.get(k) or [])
    names = getlist(f"{spec.key}_name")
    amounts = getlist(f"{spec.key}_amount")
    kinds = getlist(f"{spec.key}_kind")
    rows = []
    for index in range(max(len(names), len(amounts))):
        name = (names[index] if index < len(names) else "").strip()
        amount = (amounts[index] if index < len(amounts) else "").strip()
        kind = (kinds[index] if index < len(kinds) else "").strip()
        if name or amount:
            rows.append({"name": name, "amount": amount, "kind": kind})
    return rows[:MAX_LINE_ITEMS + 5]


def parse_line_items(rows: list[dict], spec: LineItemSpec) -> tuple[list[dict], list[str]]:
    """Validate raw rows. Returns (clean rows, error messages)."""
    clean, errors = [], []
    if len(rows) > MAX_LINE_ITEMS:
        errors.append(f"You can add up to {MAX_LINE_ITEMS} rows to {spec.title.lower()}.")
    valid_kinds = {code for code, _ in spec.kinds}
    for number, row in enumerate(rows[:MAX_LINE_ITEMS], start=1):
        name, raw_amount = row["name"], row["amount"]
        if not name:
            errors.append(f"Row {number}: please describe this item.")
            continue
        if len(name) > 80:
            errors.append(f"Row {number}: keep the description under 80 characters.")
            continue
        try:
            amount = to_decimal(raw_amount)
        except ValueError:
            errors.append(f"Row {number} ({name}): enter the amount as a number, e.g. 25000.")
            continue
        if amount is None:
            errors.append(f"Row {number} ({name}): enter an amount.")
            continue
        if amount < 0 or amount > MAX_AMOUNT:
            errors.append(f"Row {number} ({name}): the amount must be zero or more.")
            continue
        kind = row.get("kind", "")
        if valid_kinds and kind not in valid_kinds:
            kind = spec.kinds[0][0]
        clean.append({"name": name, "amount": amount, "kind": kind})
    return clean, errors


class ModelInputForm(forms.Form):
    """Base class for every model's input form."""

    project_name = forms.CharField(
        label="Project name",
        max_length=120,
        help_text="A name you will recognise later, e.g. “Lekki Bakery 2027 plan”.",
    )
    currency = forms.ChoiceField(
        label="Currency",
        choices=CURRENCY_CHOICES,
        initial=DEFAULT_CURRENCY,
        help_text="All amounts in this project use this currency. FINPLAN never converts between currencies.",
    )

    steps: tuple[Step, ...] = ()
    line_item_specs: tuple[LineItemSpec, ...] = ()
    extra_lever: ExtraLever | None = None
    scenario_names = {"conservative": "Conservative", "optimistic": "Optimistic"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.line_item_errors: dict[str, list[str]] = {}
        self._add_scenario_fields()
        for bound in self:
            bound.field.widget.attrs.setdefault("class", "input")

    # --- Scenarios ------------------------------------------------------
    def _add_scenario_fields(self):
        levers = [
            ("revenue_pct", "Income / price change (%)", "Negative values reduce income, positive values increase it.", DEFAULT_REVENUE, "-100", "500"),
            ("cost_pct", "Cost change (%)", "Positive values make costs higher, negative values lower.", DEFAULT_COST, "-100", "500"),
        ]
        if self.extra_lever:
            lever = self.extra_lever
            levers.append(("extra", lever.label, lever.help,
                           {"conservative": lever.conservative, "optimistic": lever.optimistic},
                           str(lever.min_value), str(lever.max_value)))
        for scenario in ("conservative", "optimistic"):
            for key, label, help_text, defaults, lo, hi in levers:
                name = field_name(scenario, key)
                self.fields[name] = percent(
                    f"{self.scenario_names[scenario]}: {label}", required=False,
                    help_text=help_text, min_value=lo, max_value=hi,
                )
                self.fields[name].initial = defaults[scenario]
        self._scenario_levers = levers

    def scenario_rows(self):
        return [
            {
                "label": label,
                "help": help_text,
                "conservative": self[field_name("conservative", key)],
                "optimistic": self[field_name("optimistic", key)],
            }
            for key, label, help_text, *_ in self._scenario_levers
        ]

    # --- Line items -----------------------------------------------------
    def line_item_rows(self, spec: LineItemSpec) -> list[dict]:
        if self.is_bound:
            return collect_line_item_rows(self.data, spec)
        rows = []
        for item in self.initial.get(spec.key) or []:
            rows.append({
                "name": item.get("name", ""),
                "amount": str(item.get("amount", "")),
                "kind": item.get("kind", ""),
            })
        return rows

    def clean(self):
        cleaned = super().clean()
        for spec in self.line_item_specs:
            items, errors = parse_line_items(collect_line_item_rows(self.data, spec), spec)
            cleaned[spec.key] = items
            if errors:
                self.line_item_errors[spec.key] = errors
                self.add_error(None, f"Please check the rows under “{spec.title}”.")
        for name, value in list(cleaned.items()):
            if name.startswith("scn_") and value is None:
                cleaned[name] = Decimal("0")
        return cleaned

    # --- Layout ---------------------------------------------------------
    def bound_steps(self) -> list[BoundStep]:
        specs = {spec.key: spec for spec in self.line_item_specs}
        result = []
        for number, step in enumerate(self.steps, start=1):
            fields = [self[name] for name in step.fields]
            advanced = [self[name] for name in step.advanced]
            items = [
                {"spec": specs[key], "rows": self.line_item_rows(specs[key]),
                 "errors": self.line_item_errors.get(key, [])}
                for key in step.line_items
            ]
            rows = self.scenario_rows() if step.scenarios else []
            has_errors = any(f.errors for f in fields + advanced) or any(i["errors"] for i in items)
            if step.scenarios:
                has_errors = has_errors or any(r["conservative"].errors or r["optimistic"].errors for r in rows)
            result.append(BoundStep(
                number=number, title=step.title, intro=step.intro, fields=fields,
                advanced=advanced, advanced_title=step.advanced_title, line_items=items,
                scenario_rows=rows,
                show_if_field=step.show_if[0] if step.show_if else "",
                show_if_values=",".join(step.show_if[1]) if step.show_if else "",
                has_errors=has_errors,
            ))
        return result

    def storable(self) -> dict:
        """Cleaned inputs in a JSON-safe form for saving on the Project."""
        return serialise(dict(self.cleaned_data))

    # Raw (unvalidated) data for saving a draft.
    def draft_data(self) -> dict:
        data = {}
        for name in self.fields:
            value = self.data.get(name, "")
            data[name] = value.strip() if isinstance(value, str) else value
        for spec in self.line_item_specs:
            data[spec.key] = collect_line_item_rows(self.data, spec)
        return data

    @classmethod
    def initial_from_saved(cls, inputs: dict) -> dict:
        """Saved inputs can be used directly as initial form data."""
        return dict(inputs)
