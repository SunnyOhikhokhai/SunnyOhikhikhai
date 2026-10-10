"""Reports: list, printable page and PDF download (owner only)."""
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from financial_models.common.charts import render_svg
from financial_models.common.report import Formatter
from financial_models.registry import MODELS
from projects.models import Project
from projects.views import build_report_or_none, owned_project

from .pdf import DISCLAIMER, build_pdf


@login_required
def report_list(request):
    projects = Project.objects.filter(owner=request.user, status=Project.Status.CALCULATED)
    return render(request, "reports/list.html", {"projects": projects})


def _calculated_project(request, pk):
    project = owned_project(request, pk)
    if project.is_draft:
        messages.info(request, "Finish and calculate this draft before creating a report.")
        return project, None, redirect("financial_models:edit", pk=project.pk)
    return project, MODELS[project.model_type], None


@login_required
def report_print(request, pk: int):
    project, spec, early = _calculated_project(request, pk)
    if early:
        return early
    report, error = build_report_or_none(project)
    fmt = Formatter(project.currency)
    charts = [(chart, render_svg(chart, fmt)) for chart in report.charts] if report else []
    return render(request, "reports/print.html", {
        "project": project, "spec": spec, "report": report, "error": error, "charts": charts,
        "generated": timezone.localtime(), "disclaimer": DISCLAIMER,
    })


@login_required
def report_pdf(request, pk: int):
    project, spec, early = _calculated_project(request, pk)
    if early:
        return early
    report, error = build_report_or_none(project, style="code")
    if report is None:
        messages.error(request, error)
        return redirect("projects:detail", pk=project.pk)
    pdf = build_pdf(project, report, spec.label)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", project.name).strip("-").lower() or "project"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="finplan-{slug}.pdf"'
    response["Cache-Control"] = "private, no-store"
    return response
