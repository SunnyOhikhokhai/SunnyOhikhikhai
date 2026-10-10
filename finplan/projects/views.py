"""Views for listing, viewing, duplicating and deleting saved projects."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from financial_models.common.charts import render_svg
from financial_models.common.money import MissingInputError
from financial_models.common.report import Formatter
from financial_models.registry import MODELS, build_project_report

from .models import Project


def owned_project(request, pk: int) -> Project:
    """Fetch a project only if it belongs to the signed-in user (404 otherwise)."""
    return get_object_or_404(Project, pk=pk, owner=request.user)


def build_report_or_none(project: Project, style: str = "symbol"):
    """Return (report, error message). Invalid saved data never crashes a page."""
    try:
        return build_project_report(project, style), ""
    except MissingInputError as exc:
        return None, f"This project is missing a required input: {exc.label}."
    except (ValueError, ArithmeticError, KeyError, TypeError):
        return None, "This project's saved inputs could not be calculated. Please review and save them again."


@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user)
    model_filter = request.GET.get("type", "")
    if model_filter in MODELS:
        projects = projects.filter(model_type=model_filter)
    else:
        model_filter = ""
    return render(request, "projects/list.html", {
        "projects": projects, "models": MODELS.values(), "model_filter": model_filter,
    })


@login_required
def project_detail(request, pk: int):
    project = owned_project(request, pk)
    if project.is_draft:
        messages.info(request, "This project is a draft. Complete the remaining steps and calculate to see results.")
        return redirect("financial_models:edit", pk=project.pk)
    report, error = build_report_or_none(project)
    fmt = Formatter(project.currency)
    charts = [(chart, render_svg(chart, fmt)) for chart in report.charts] if report else []
    return render(request, "projects/detail.html", {
        "project": project, "spec": MODELS[project.model_type], "report": report, "error": error, "charts": charts,
    })


@login_required
@require_POST
def project_duplicate(request, pk: int):
    original = owned_project(request, pk)
    copy = Project.objects.create(
        owner=request.user,
        name=f"Copy of {original.name}"[:120],
        model_type=original.model_type,
        currency=original.currency,
        status=original.status,
        inputs={**original.inputs, "project_name": f"Copy of {original.name}"[:120]},
        last_calculated_at=original.last_calculated_at,
    )
    messages.success(request, f"Created “{copy.name}”. Change its assumptions to test an alternative plan.")
    return redirect("financial_models:edit", pk=copy.pk)


@login_required
def project_delete(request, pk: int):
    project = owned_project(request, pk)
    if request.method == "POST":
        name = project.name
        project.delete()
        messages.success(request, f"“{name}” has been deleted.")
        return redirect("projects:list")
    return render(request, "projects/confirm_delete.html", {"project": project})
