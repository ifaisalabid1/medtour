from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from apps.content.selectors import (
    faqs_for_treatment,
    published_articles,
    testimonials_for_treatment,
    testimonials_from_country,
)

pytestmark = pytest.mark.django_db


def test_published_articles_are_newest_first_and_drafts_hidden():
    older = baker.make_recipe("apps.content.tests.article")
    older.published_at = timezone.now() - timedelta(days=3)
    older.save()
    newer = baker.make_recipe("apps.content.tests.article")
    baker.make_recipe("apps.content.tests.article", is_published=False)

    assert list(published_articles()) == [newer, older]


def test_faqs_for_treatment_are_ordered_and_exclude_unpublished():
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    second = baker.make_recipe(
        "apps.content.tests.faq", treatment=treatment, display_order=2
    )
    first = baker.make_recipe(
        "apps.content.tests.faq", treatment=treatment, display_order=1
    )
    baker.make_recipe("apps.content.tests.faq", treatment=treatment, is_published=False)
    baker.make_recipe("apps.content.tests.faq")  # another treatment's FAQ

    assert list(faqs_for_treatment(treatment)) == [first, second]


def test_testimonials_by_treatment_and_by_country():
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    from_bangladesh = baker.make_recipe(
        "apps.content.tests.testimonial", country="BD", treatment=treatment
    )
    from_nigeria = baker.make_recipe("apps.content.tests.testimonial", country="NG")
    baker.make_recipe(
        "apps.content.tests.testimonial",
        country="BD",
        treatment=treatment,
        is_published=False,
    )

    assert list(testimonials_for_treatment(treatment)) == [from_bangladesh]
    assert list(testimonials_from_country("NG")) == [from_nigeria]
