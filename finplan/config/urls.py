"""Top-level URL routes for FINPLAN."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("dashboard.urls")),
    path("accounts/", include("accounts.urls")),
    path("models/", include("financial_models.urls")),
    path("projects/", include("projects.urls")),
    path("reports/", include("reports.urls")),
    path("admin/", admin.site.urls),
]
