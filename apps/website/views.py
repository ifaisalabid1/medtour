"""Public pages. Each view loads published data through selectors and renders.

Views only compose: what counts as "published" is decided by the selectors,
and an old or unknown slug is handled by get_object_or_redirect.

Every page also gets `structured_data` (JSON-LD, rendered by base.html) and,
where relevant, `noindex` to keep thin pages out of search results.
"""

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

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

from . import structured_data as schema
from .seo import is_indexable, meta_description

FEATURED_LIMIT = 12
HOME = ("Home", "/")


def speciality_detail(request, slug):
    speciality = get_object_or_redirect(published_specialities(), slug)
    return render(
        request,
        "website/speciality_detail.html",
        {
            "speciality": speciality,
            "meta_description": meta_description(speciality.summary),
            "treatments": with_starting_price(treatments_in_speciality(speciality)),
            "hospitals": hospitals_for_speciality(speciality)[:FEATURED_LIMIT],
            "doctors": doctors_for_speciality(speciality)[:FEATURED_LIMIT],
            "structured_data": [
                schema.breadcrumbs(
                    HOME, (speciality.name, speciality.get_absolute_url())
                ),
            ],
        },
    )


def treatment_detail(request, slug):
    treatment = get_object_or_redirect(published_treatments(), slug)
    faqs = list(faqs_for_treatment(treatment))
    speciality = treatment.speciality
    return render(
        request,
        "website/treatment_detail.html",
        {
            "treatment": treatment,
            "meta_description": meta_description(
                treatment.summary,
                f"Indicative cost of {treatment.name} in India, with prices "
                "from partner hospitals.",
            ),
            "cost": cost_summary(treatment),
            "packages": packages_for_treatment(treatment),
            "faqs": faqs,
            "testimonials": testimonials_for_treatment(treatment)[:6],
            "articles": articles_about_treatment(treatment)[:3],
            "noindex": not is_indexable(treatment),
            "structured_data": _present(
                schema.medical_procedure(treatment),
                schema.faq_page(faqs),
                schema.breadcrumbs(
                    HOME,
                    (speciality.name, speciality.get_absolute_url()),
                    (treatment.name, treatment.get_absolute_url()),
                ),
            ),
        },
    )


def condition_detail(request, slug):
    condition = get_object_or_redirect(published_conditions(), slug)
    treatments = list(with_starting_price(treatments_for_condition(condition)))
    faqs = list(faqs_for_condition(condition))
    return render(
        request,
        "website/condition_detail.html",
        {
            "condition": condition,
            "meta_description": meta_description(condition.summary),
            "treatments": treatments,
            "faqs": faqs,
            "structured_data": _present(
                schema.medical_condition(condition, treatments),
                schema.faq_page(faqs),
                schema.breadcrumbs(
                    HOME, (condition.name, condition.get_absolute_url())
                ),
            ),
        },
    )


def hospital_detail(request, slug):
    hospital = get_object_or_redirect(published_hospitals(), slug)
    return render(
        request,
        "website/hospital_detail.html",
        {
            "hospital": hospital,
            "meta_description": meta_description(hospital.summary),
            "packages": packages_at_hospital(hospital),
            "doctors": doctors_at_hospital(hospital)[:FEATURED_LIMIT],
            "structured_data": [
                schema.hospital(hospital),
                schema.breadcrumbs(HOME, (hospital.name, hospital.get_absolute_url())),
            ],
        },
    )


def doctor_detail(request, slug):
    doctor = get_object_or_redirect(published_doctors(), slug)
    return render(
        request,
        "website/doctor_detail.html",
        {
            "doctor": doctor,
            "meta_description": meta_description(doctor.summary, doctor.designation),
            "structured_data": [
                schema.physician(doctor),
                schema.breadcrumbs(HOME, (str(doctor), doctor.get_absolute_url())),
            ],
        },
    )


def corridor_detail(request, slug):
    """A source-country page, e.g. "medical travel from Bangladesh to India"."""
    source_country = get_object_or_redirect(published_source_countries(), slug)
    title = f"Medical travel from {source_country.country.name} to India"
    return render(
        request,
        "website/corridor_detail.html",
        {
            "source_country": source_country,
            "meta_description": meta_description(source_country.intro),
            "testimonials": testimonials_from_country(source_country.country.code)[:6],
            "structured_data": [
                schema.breadcrumbs(HOME, (title, source_country.get_absolute_url())),
            ],
        },
    )


def article_detail(request, slug):
    article = get_object_or_redirect(published_articles(), slug)
    return render(
        request,
        "website/article_detail.html",
        {
            "article": article,
            "meta_description": meta_description(article.summary),
            "structured_data": [
                schema.medical_web_page(article),
                schema.breadcrumbs(HOME, (article.title, article.get_absolute_url())),
            ],
        },
    )


@require_GET
def robots_txt(request):
    """Allow crawling of public pages and point crawlers to the sitemap.

    The admin's address is deliberately not listed: robots.txt is public,
    and the admin URL is kept private in production. It's behind a login
    anyway, so crawlers can't index it.
    """
    lines = [
        "User-agent: *",
        "Disallow: /staff/",
        "",
        f"Sitemap: {settings.SITE_URL}{reverse('website:sitemap_index')}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def _present(*items):
    """Drop structured-data blocks that don't apply (e.g. no FAQs)."""
    return [item for item in items if item]
