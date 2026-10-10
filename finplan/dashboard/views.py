"""Landing page and the signed-in user's dashboard."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from financial_models.registry import MODELS
from projects.models import Project


def landing(request):
    return render(request, "dashboard/landing.html", {"models": MODELS.values()})


@login_required
def home(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, "dashboard/home.html", {
        "models": MODELS.values(),
        "recent": projects[:5],
        "forecasts": projects.filter(status=Project.Status.CALCULATED)[:6],
        "drafts": projects.filter(status=Project.Status.DRAFT)[:5],
        "project_count": projects.count(),
    })
