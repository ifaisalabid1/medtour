import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


def make_package(treatment, **fields):
    return baker.make_recipe(
        "apps.pricing.tests.package", treatment=treatment, **fields
    )


def test_home_page_shows_priced_treatments_and_compares_hospitals(client):
    knee = baker.make_recipe("apps.catalog.tests.treatment", name="Knee replacement")
    make_package(knee, price_min_inr=250_000)
    make_package(knee, price_min_inr=300_000)
    baker.make_recipe("apps.catalog.tests.treatment", name="Unpriced treatment")

    response = client.get(reverse("website:home"))

    assert response.context["hero_treatment"] == knee
    assert len(response.context["hero_packages"]) == 2
    assert [t.name for t in response.context["treatments"]] == ["Knee replacement"]
    assert "₹2,50,000" in response.content.decode()


def test_home_page_works_before_any_content_exists(client):
    response = client.get(reverse("website:home"))

    assert response.status_code == 200
    assert response.context["hero_treatment"] is None
    assert b'id="treatments"' not in response.content


def test_home_page_lists_published_specialities_with_their_icons(client):
    baker.make_recipe(
        "apps.catalog.tests.speciality", name="Cardiology", icon="heart-pulse"
    )
    baker.make_recipe(
        "apps.catalog.tests.speciality", name="Hidden", is_published=False
    )

    content = client.get(reverse("website:home")).content.decode()

    assert "Cardiology" in content
    assert "icons.svg#heart-pulse" in content
    assert "Hidden" not in content


def test_home_page_describes_the_organisation_for_search_engines(client):
    response = client.get(reverse("website:home"))

    types = [block["@type"] for block in response.context["structured_data"]]
    assert types == ["Organization", "WebSite"]
    assert response.context["meta_description"]


def test_home_page_query_count_does_not_grow_with_content(
    client, django_assert_num_queries
):
    for _ in range(6):
        treatment = baker.make_recipe("apps.catalog.tests.treatment")
        for _ in range(3):
            make_package(treatment)
    baker.make_recipe("apps.catalog.tests.speciality", _quantity=8)

    # Treatments, exchange rate, hero packages, their accreditations, specialities.
    with django_assert_num_queries(5):
        client.get(reverse("website:home"))


def test_only_the_medical_opinion_card_is_highlighted(client):
    """Guards cotton flags: an unquoted dark=False quoted by a formatter becomes
    the string "False", which is truthy and darkens every card."""
    content = client.get(reverse("website:home")).content.decode()

    assert content.count("border-brand-950 bg-brand-950") == 1
