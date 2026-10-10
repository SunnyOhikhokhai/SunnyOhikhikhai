from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "model_type", "currency", "status", "owner", "updated_at")
    list_filter = ("model_type", "status", "currency")
    search_fields = ("name", "owner__username")
    readonly_fields = ("created_at", "updated_at", "last_calculated_at")
