from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("<int:pk>/print/", views.report_print, name="print"),
    path("<int:pk>/pdf/", views.report_pdf, name="pdf"),
]
