from django.urls import path

from . import views

app_name = "financial_models"

urlpatterns = [
    path("", views.choose_model, name="choose"),
    path("<slug:model_type>/new/", views.new_project, name="new"),
    path("project/<int:pk>/edit/", views.edit_project, name="edit"),
]
