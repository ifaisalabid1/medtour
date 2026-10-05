import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from model_bakery import baker

from apps.catalog.models import Treatment

pytestmark = pytest.mark.django_db


@pytest.fixture
def treatment():
    return baker.make_recipe(
        "apps.catalog.tests.treatment", name="Knee replacement", slug="knee-replacement"
    )


@pytest.mark.parametrize(
    ("recipe", "fields", "expected_url"),
    [
        (
            "apps.catalog.tests.treatment",
            {"slug": "knee-replacement"},
            "/treatments/knee-replacement-cost-in-india/",
        ),
        (
            "apps.catalog.tests.speciality",
            {"slug": "orthopaedics"},
            "/specialities/orthopaedics/",
        ),
        (
            "apps.catalog.tests.condition",
            {"slug": "osteoarthritis"},
            "/conditions/osteoarthritis/",
        ),
        (
            "apps.providers.tests.hospital",
            {"slug": "apollo-chennai"},
            "/hospitals/apollo-chennai/",
        ),
        (
            "apps.providers.tests.doctor",
            {"slug": "naresh-trehan"},
            "/doctors/naresh-trehan/",
        ),
        (
            "apps.locations.tests.source_country",
            {"country": "BD", "slug": "bangladesh"},
            "/medical-travel-from-bangladesh-to-india/",
        ),
        (
            "apps.content.tests.article",
            {"slug": "knee-recovery"},
            "/knowledge/knee-recovery/",
        ),
    ],
)
def test_every_public_page_has_a_working_url(client, recipe, fields, expected_url):
    page = baker.make_recipe(recipe, **fields)

    assert page.get_absolute_url() == expected_url
    assert client.get(expected_url).status_code == 200


def test_unpublished_pages_are_not_found(client, treatment):
    Treatment.objects.filter(pk=treatment.pk).update(is_published=False)

    assert client.get(treatment.get_absolute_url()).status_code == 404


def test_treatments_of_a_hidden_speciality_are_not_found(client, treatment):
    treatment.speciality.is_published = False
    treatment.speciality.save()

    assert client.get(treatment.get_absolute_url()).status_code == 404


def test_old_url_permanently_redirects_after_a_slug_change(client, treatment):
    old_url = treatment.get_absolute_url()
    treatment.slug = "total-knee-replacement"
    treatment.save()

    response = client.get(old_url)

    assert response.status_code == 301
    assert response["Location"] == "/treatments/total-knee-replacement-cost-in-india/"


def test_treatment_page_shows_public_prices_only(client, treatment):
    baker.make_recipe(
        "apps.pricing.tests.package", treatment=treatment, price_min_inr=250_000
    )
    baker.make_recipe(
        "apps.pricing.tests.package",
        treatment=treatment,
        price_min_inr=90_000,
        is_published=False,
    )

    response = client.get(treatment.get_absolute_url())

    assert "₹2,50,000" in response.text
    assert "₹90,000" not in response.text
    assert len(response.context["packages"]) == 1


def count_queries(client, url):
    with CaptureQueriesContext(connection) as queries:
        client.get(url)
    return len(queries)


def test_treatment_page_query_count_does_not_grow_with_content(client, treatment):
    def add_content():
        baker.make_recipe("apps.pricing.tests.package", treatment=treatment)
        baker.make_recipe("apps.content.tests.faq", treatment=treatment)
        baker.make_recipe("apps.content.tests.testimonial", treatment=treatment)

    add_content()
    with_one_of_each = count_queries(client, treatment.get_absolute_url())
    for _ in range(4):
        add_content()
    with_five_of_each = count_queries(client, treatment.get_absolute_url())

    # Extra rows must not mean extra queries (no "N+1" queries per row).
    assert with_five_of_each == with_one_of_each


def test_admin_view_on_site_link_opens_the_public_page(admin_client, treatment):
    content_type = ContentType.objects.get_for_model(Treatment)
    url = reverse("admin:view_on_site", args=[content_type.pk, treatment.pk])

    response = admin_client.get(url)

    assert response.status_code == 302
    assert response["Location"].endswith(treatment.get_absolute_url())
