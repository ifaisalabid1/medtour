import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:content_author_changelist",
        "admin:content_author_add",
        "admin:content_article_changelist",
        "admin:content_article_add",
        "admin:content_faq_changelist",
        "admin:content_faq_add",
        "admin:content_testimonial_changelist",
        "admin:content_testimonial_add",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    baker.make_recipe("apps.content.tests.article")
    baker.make_recipe("apps.content.tests.faq")
    baker.make_recipe("apps.content.tests.testimonial")

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_admin_cleans_rich_text_when_saving(admin_client):
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    url = reverse("admin:catalog_treatment_change", args=[treatment.pk])

    response = admin_client.post(
        url,
        {
            "speciality": treatment.speciality.pk,
            "name": treatment.name,
            "slug": treatment.slug,
            "is_published": "on",
            "description": '<p>Safe</p><script>alert("x")</script>',
            "conditions-TOTAL_FORMS": "0",
        },
    )

    assert response.status_code == 302, response.context["adminform"].form.errors
    treatment.refresh_from_db()
    assert treatment.description == "<p>Safe</p>"
