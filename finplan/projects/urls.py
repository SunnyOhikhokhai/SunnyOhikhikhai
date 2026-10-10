from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.project_list, name="list"),
    path("<int:pk>/", views.project_detail, name="detail"),
    path("<int:pk>/duplicate/", views.project_duplicate, name="duplicate"),
    path("<int:pk>/delete/", views.project_delete, name="delete"),
]
