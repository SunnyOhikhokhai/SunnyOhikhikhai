"""
One place that lists the four financial models.

Views, templates and reports look models up here, so adding a fifth model
means adding one entry rather than editing many files.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .business.forms import BusinessForm
from .business.report import build_report as business_report
from .common.report import Formatter, Report
from .investment.forms import InvestmentForm
from .investment.report import build_report as investment_report
from .real_estate.forms import RealEstateForm
from .real_estate.report import build_report as real_estate_report
from .startup.forms import StartupForm
from .startup.report import build_report as startup_report


@dataclass(frozen=True)
class ModelSpec:
    key: str
    label: str
    short_label: str
    icon: str
    summary: str
    audience: str
    form_class: type
    build_report: Callable[[dict, Formatter], Report]


MODELS: dict[str, ModelSpec] = {
    spec.key: spec
    for spec in (
        ModelSpec("business", "Business Financial Model", "Business", "business",
                  "Understand your revenue, costs, profit and break-even point, with a 12-month forecast.",
                  "For existing businesses", BusinessForm, business_report),
        ModelSpec("startup", "Startup Financial Model", "Startup", "startup",
                  "See how much money you need to launch, how long it may last and when you could break even.",
                  "For founders and new ventures", StartupForm, startup_report),
        ModelSpec("real_estate", "Real Estate Financial Model", "Real estate", "real_estate",
                  "Check whether a property development, land subdivision or rental project could be worthwhile.",
                  "For developers and property investors", RealEstateForm, real_estate_report),
        ModelSpec("investment", "Investment Financial Model", "Investment", "investment",
                  "Compare potential returns using ROI, annualised return, NPV and IRR, with best and worst cases.",
                  "For investors", InvestmentForm, investment_report),
    )
}


def get_model(key: str) -> ModelSpec | None:
    return MODELS.get(key)


def build_project_report(project, style: str = "symbol") -> Report:
    """Recalculate a saved project's report from its stored inputs."""
    spec = MODELS[project.model_type]
    return spec.build_report(project.inputs, Formatter(project.currency, style))
