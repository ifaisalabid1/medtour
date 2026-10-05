from datetime import date

import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from apps.content.models import FAQ, Article, Testimonial

pytestmark = pytest.mark.django_db


def test_article_cannot_be_published_without_medical_review():
    article = baker.prepare_recipe(
        "apps.content.tests.article",
        medical_reviewer=None,
        reviewed_on=None,
        _save_related=True,
    )

    with pytest.raises(ValidationError, match="medical reviewer"):
        article.full_clean()


def test_unpublished_draft_does_not_need_a_review_yet():
    draft = baker.prepare_recipe(
        "apps.content.tests.article",
        medical_reviewer=None,
        reviewed_on=None,
        is_published=False,
        _save_related=True,
    )

    draft.full_clean()  # must not raise


def test_medical_reviewer_must_be_a_medical_professional():
    not_a_doctor = baker.make_recipe("apps.content.tests.author")
    article = baker.prepare_recipe(
        "apps.content.tests.article", medical_reviewer=not_a_doctor, _save_related=True
    )

    with pytest.raises(ValidationError) as exc:
        article.full_clean()

    assert "medical_reviewer" in exc.value.message_dict


def test_published_at_is_set_on_first_publish_and_then_kept():
    article = baker.make_recipe("apps.content.tests.article", is_published=False)
    assert article.published_at is None

    article.is_published = True
    article.save()
    first_published = article.published_at

    article.title = "Updated title"
    article.save()

    assert first_published is not None
    assert Article.objects.get(pk=article.pk).published_at == first_published


@pytest.mark.parametrize("parents", ["none", "both"])
def test_faq_belongs_to_exactly_one_page(parents):
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    condition = baker.make_recipe("apps.catalog.tests.condition")
    faq = FAQ(
        question="How long is the recovery?",
        answer="<p>About six weeks.</p>",
        treatment=treatment if parents == "both" else None,
        condition=condition if parents == "both" else None,
    )

    with pytest.raises(ValidationError, match="either a treatment or a condition"):
        faq.full_clean()


def test_testimonial_cannot_be_published_without_consent():
    testimonial = Testimonial(
        patient_display_name="Rahim U.",
        country="BD",
        quote="Excellent care.",
        is_published=True,
    )

    with pytest.raises(ValidationError, match="consent"):
        testimonial.full_clean()

    testimonial.consent_obtained_on = date(2026, 9, 1)
    testimonial.full_clean()  # now allowed
