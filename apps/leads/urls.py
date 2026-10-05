from django.urls import path

from . import views

app_name = "leads"

urlpatterns = [
    path(
        "documents/<int:pk>/download/",
        views.download_document,
        name="download_document",
    ),
]
