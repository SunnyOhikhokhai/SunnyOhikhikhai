"""
Model workspace views: choose a model, fill in the guided form, save as a
draft, or calculate and save.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from projects.models import Project

from .common.money import CURRENCIES, DEFAULT_CURRENCY
from .registry import MODELS, get_model


@login_required
def choose_model(request):
    return render(request, "financial_models/choose.html", {"models": MODELS.values()})


def _initial_from_project(project: Project) -> dict:
    initial = {k: v for k, v in (project.inputs or {}).items() if v not in ("", None, [])}
    initial["project_name"] = project.name
    initial["currency"] = project.currency
    return initial


def _save_draft(request, spec, form, project: Project | None) -> Project:
    data = form.draft_data()
    name = (data.get("project_name") or "").strip()[:120] or f"Untitled {spec.short_label.lower()} plan"
    currency = data.get("currency") if data.get("currency") in CURRENCIES else DEFAULT_CURRENCY
    if project is None:
        project = Project(owner=request.user, model_type=spec.key)
    project.name = name
    project.currency = currency
    project.inputs = data
    project.status = Project.Status.DRAFT
    project.save()
    return project


def _workspace(request, spec, project: Project | None):
    form_class = spec.form_class
    if request.method == "POST":
        form = form_class(request.POST)
        if request.POST.get("action") == "draft":
            project = _save_draft(request, spec, form, project)
            messages.success(request, f"Draft “{project.name}” saved. You can finish it any time from your dashboard.")
            return redirect("financial_models:edit", pk=project.pk)
        if form.is_valid():
            if project is None:
                project = Project(owner=request.user, model_type=spec.key)
            project.name = form.cleaned_data["project_name"]
            project.currency = form.cleaned_data["currency"]
            project.inputs = form.storable()
            project.status = Project.Status.CALCULATED
            project.last_calculated_at = timezone.now()
            project.save()
            messages.success(request, "Your results have been calculated and saved.")
            return redirect("projects:detail", pk=project.pk)
        messages.error(request, "Some answers need attention. Please check the highlighted fields.")
    elif project is not None:
        form = form_class(initial=_initial_from_project(project))
    else:
        form = form_class()

    current = form["currency"].value()
    current = current if current in CURRENCIES else DEFAULT_CURRENCY
    return render(request, "financial_models/workspace.html", {
        "spec": spec,
        "form": form,
        "project": project,
        "steps": form.bound_steps(),
        "currency_symbols": {code: info["symbol"] for code, info in CURRENCIES.items()},
        "current_symbol": CURRENCIES[current]["symbol"],
    })


@login_required
def new_project(request, model_type: str):
    spec = get_model(model_type)
    if spec is None:
        raise Http404("Unknown financial model")
    return _workspace(request, spec, None)


@login_required
def edit_project(request, pk: int):
    # Ownership check: a user can only ever load their own projects.
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    return _workspace(request, MODELS[project.model_type], project)
