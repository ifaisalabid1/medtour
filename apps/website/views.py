"""Public pages. Each view loads published data through selectors and renders.

Views only compose: what counts as "published" is decided by the selectors,
and an old or unknown slug is handled by get_object_or_redirect.
"""

from django.shortcuts import render

from apps.catalog.selectors import (
    published_conditions,
    published_specialities,
    published_treatments,
    treatments_for_condition,
    treatments_in_speciality,
)
from apps.content.selectors import (
    articles_about_treatment,
    faqs_for_condition,
    faqs_for_treatment,
    published_articles,
    testimonials_for_treatment,
    testimonials_from_country,
)
from apps.core.redirects import get_object_or_redirect
from apps.locations.selectors import published_source_countries
from apps.pricing.selectors import (
    cost_summary,
    packages_at_hospital,
    packages_for_treatment,
    with_starting_price,
)
from apps.providers.selectors import (
    doctors_at_hospital,
    doctors_for_speciality,
    hospitals_for_speciality,
    published_doctors,
    published_hospitals,
)

FEATURED_LIMIT = 12


def speciality_detail(request, slug):
    speciality = get_object_or_redirect(published_specialities(), slug)
    return render(
        request,
        "website/speciality_detail.html",
        {
            "speciality": speciality,
            "treatments": with_starting_price(treatments_in_speciality(speciality)),
            "hospitals": hospitals_for_speciality(speciality)[:FEATURED_LIMIT],
            "doctors": doctors_for_speciality(speciality)[:FEATURED_LIMIT],
        },
    )


def treatment_detail(request, slug):
    treatment = get_object_or_redirect(published_treatments(), slug)
    return render(
        request,
        "website/treatment_detail.html",
        {
            "treatment": treatment,
            "cost": cost_summary(treatment),
            "packages": packages_for_treatment(treatment),
            "faqs": faqs_for_treatment(treatment),
            "testimonials": testimonials_for_treatment(treatment)[:6],
            "articles": articles_about_treatment(treatment)[:3],
        },
    )


def condition_detail(request, slug):
    condition = get_object_or_redirect(published_conditions(), slug)
    return render(
        request,
        "website/condition_detail.html",
        {
            "condition": condition,
            "treatments": with_starting_price(treatments_for_condition(condition)),
            "faqs": faqs_for_condition(condition),
        },
    )


def hospital_detail(request, slug):
    hospital = get_object_or_redirect(published_hospitals(), slug)
    return render(
        request,
        "website/hospital_detail.html",
        {
            "hospital": hospital,
            "packages": packages_at_hospital(hospital),
            "doctors": doctors_at_hospital(hospital)[:FEATURED_LIMIT],
        },
    )


def doctor_detail(request, slug):
    doctor = get_object_or_redirect(published_doctors(), slug)
    return render(request, "website/doctor_detail.html", {"doctor": doctor})


def corridor_detail(request, slug):
    """A source-country page, e.g. "medical travel from Bangladesh to India"."""
    source_country = get_object_or_redirect(published_source_countries(), slug)
    return render(
        request,
        "website/corridor_detail.html",
        {
            "source_country": source_country,
            "testimonials": testimonials_from_country(source_country.country.code)[:6],
        },
    )


def article_detail(request, slug):
    article = get_object_or_redirect(published_articles(), slug)
    return render(request, "website/article_detail.html", {"article": article})
