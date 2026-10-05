from django.db.models import QuerySet

from apps.catalog.models import Condition, Treatment

from .models import FAQ, Article, Testimonial


def published_articles() -> QuerySet[Article]:
    """Newest first, with author and reviewer loaded for the byline."""
    return (
        Article.objects.published()
        .select_related("author", "medical_reviewer")
        .order_by("-published_at")
    )


def faqs_for_treatment(treatment: Treatment) -> QuerySet[FAQ]:
    return FAQ.objects.published().filter(treatment=treatment)


def faqs_for_condition(condition: Condition) -> QuerySet[FAQ]:
    return FAQ.objects.published().filter(condition=condition)


def published_testimonials() -> QuerySet[Testimonial]:
    return Testimonial.objects.published().select_related(
        "treatment", "hospital__city", "doctor"
    )


def testimonials_for_treatment(treatment: Treatment) -> QuerySet[Testimonial]:
    return published_testimonials().filter(treatment=treatment)


def testimonials_from_country(country_code: str) -> QuerySet[Testimonial]:
    """For pages like "medical travel from Bangladesh to India"."""
    return published_testimonials().filter(country=country_code)


def articles_about_treatment(treatment: Treatment) -> QuerySet[Article]:
    return published_articles().filter(treatments=treatment)
