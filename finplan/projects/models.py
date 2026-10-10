"""
Saved financial projects.

A project stores the user's *inputs* only. Results are recalculated from
those inputs every time they are viewed, so a saved project always
reproduces the same results from the same calculation logic.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse

from financial_models.common.money import CURRENCY_CHOICES, DEFAULT_CURRENCY


class Project(models.Model):
    class ModelType(models.TextChoices):
        BUSINESS = "business", "Business Financial Model"
        STARTUP = "startup", "Startup Financial Model"
        REAL_ESTATE = "real_estate", "Real Estate Financial Model"
        INVESTMENT = "investment", "Investment Financial Model"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CALCULATED = "calculated", "Calculated"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=120)
    model_type = models.CharField(max_length=20, choices=ModelType.choices)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=DEFAULT_CURRENCY)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    inputs = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["owner", "-updated_at"])]

    def __str__(self) -> str:
        return self.name

    @property
    def is_draft(self) -> bool:
        return self.status == self.Status.DRAFT

    def get_absolute_url(self) -> str:
        if self.is_draft:
            return reverse("financial_models:edit", args=[self.pk])
        return reverse("projects:detail", args=[self.pk])
