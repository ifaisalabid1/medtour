from django.urls import path

from . import views

app_name = "website"

# Lowercase, hyphenated, keyword-first URLs, as the SEO plan recommends.
urlpatterns = [
    path(
        "treatments/<slug:slug>-cost-in-india/",
        views.treatment_detail,
        name="treatment_detail",
    ),
    path(
        "specialities/<slug:slug>/",
        views.speciality_detail,
        name="speciality_detail",
    ),
    path("conditions/<slug:slug>/", views.condition_detail, name="condition_detail"),
    path("hospitals/<slug:slug>/", views.hospital_detail, name="hospital_detail"),
    path("doctors/<slug:slug>/", views.doctor_detail, name="doctor_detail"),
    path(
        "medical-travel-from-<slug:slug>-to-india/",
        views.corridor_detail,
        name="corridor_detail",
    ),
    path("knowledge/<slug:slug>/", views.article_detail, name="article_detail"),
]
