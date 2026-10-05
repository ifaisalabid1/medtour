"""Schema.org structured data (JSON-LD) for public pages.

Search engines and AI answer engines read this to understand what a page is
about: a procedure, a hospital, a doctor, a reviewed medical article.
Only facts we actually hold are included; nothing is padded or guessed.
"""

from django.conf import settings

SCHEMA_CONTEXT = "https://schema.org"


def absolute_url(path_or_url: str) -> str:
    """Turn a site path (or a storage URL) into an absolute URL."""
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    return f"{settings.SITE_URL}{path_or_url}"


def _names(also_known_as: str) -> list[str]:
    return [name.strip() for name in also_known_as.split(",") if name.strip()]


def _with_optional(data: dict, **optional) -> dict:
    """Add only the optional properties that have a value."""
    data.update({key: value for key, value in optional.items() if value})
    return data


def breadcrumbs(*crumbs: tuple[str, str]) -> dict:
    """BreadcrumbList from (name, path) pairs, home page first."""
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": name,
                "item": absolute_url(path),
            }
            for position, (name, path) in enumerate(crumbs, start=1)
        ],
    }


def medical_procedure(treatment) -> dict:
    return _with_optional(
        {
            "@context": SCHEMA_CONTEXT,
            "@type": "MedicalProcedure",
            "name": treatment.name,
            "url": absolute_url(treatment.get_absolute_url()),
        },
        description=treatment.summary,
        alternateName=_names(treatment.also_known_as),
    )


def faq_page(faqs) -> dict | None:
    """FAQPage for a list of FAQs, or None when there are none."""
    if not faqs:
        return None
    return {
        "@context": SCHEMA_CONTEXT,
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                # Answers are sanitised HTML; FAQ markup allows basic HTML.
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }


def medical_condition(condition, treatments) -> dict:
    return _with_optional(
        {
            "@context": SCHEMA_CONTEXT,
            "@type": "MedicalCondition",
            "name": condition.name,
            "url": absolute_url(condition.get_absolute_url()),
        },
        description=condition.summary,
        alternateName=_names(condition.also_known_as),
        possibleTreatment=[
            {
                "@type": "MedicalProcedure",
                "name": treatment.name,
                "url": absolute_url(treatment.get_absolute_url()),
            }
            for treatment in treatments
        ],
    )


def hospital(hospital) -> dict:
    address = _with_optional(
        {
            "@type": "PostalAddress",
            "addressLocality": hospital.city.name,
            "addressRegion": hospital.city.state,
            "addressCountry": "IN",
        },
        streetAddress=hospital.address,
        postalCode=hospital.postal_code,
    )
    return _with_optional(
        {
            "@context": SCHEMA_CONTEXT,
            "@type": "Hospital",
            "name": hospital.name,
            "url": absolute_url(hospital.get_absolute_url()),
            "address": address,
        },
        description=hospital.summary,
        alternateName=_names(hospital.also_known_as),
        image=absolute_url(hospital.image.url) if hospital.image else None,
        foundingDate=str(hospital.established_year or ""),
    )


def physician(doctor) -> dict:
    """An individual doctor. Expects a doctor from published_doctors(), so
    only their public hospitals are listed."""
    return _with_optional(
        {
            "@context": SCHEMA_CONTEXT,
            "@type": "IndividualPhysician",
            "name": f"Dr. {doctor.name}",
            "url": absolute_url(doctor.get_absolute_url()),
        },
        description=doctor.summary,
        image=absolute_url(doctor.photo.url) if doctor.photo else None,
        hospitalAffiliation=[
            {
                "@type": "Hospital",
                "name": hospital.name,
                "url": absolute_url(hospital.get_absolute_url()),
            }
            for hospital in doctor.public_hospitals
        ],
    )


def medical_web_page(article) -> dict:
    """A medically reviewed article: who wrote it, who reviewed it and when."""
    return _with_optional(
        {
            "@context": SCHEMA_CONTEXT,
            "@type": "MedicalWebPage",
            "headline": article.title,
            "url": absolute_url(article.get_absolute_url()),
            "description": article.summary,
            "author": {"@type": "Person", "name": article.author.name},
            "reviewedBy": {"@type": "Person", "name": article.medical_reviewer.name},
            "lastReviewed": article.reviewed_on.isoformat(),
            "datePublished": article.published_at.isoformat(),
            "dateModified": article.updated_at.isoformat(),
        },
        image=absolute_url(article.cover_image.url) if article.cover_image else None,
    )
