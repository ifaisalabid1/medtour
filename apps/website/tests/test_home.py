import re

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

pytestmark = pytest.mark.django_db


HTMX_PARTIAL = {"HX-Request": "true", "HX-Request-Type": "partial"}


def make_package(treatment, **fields):
    return baker.make_recipe(
        "apps.pricing.tests.package", treatment=treatment, **fields
    )


def make_hospital(**fields):
    return baker.make_recipe("apps.providers.tests.hospital", **fields)


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

    for doctor in baker.make_recipe("apps.providers.tests.doctor", _quantity=4):
        doctor.hospitals.add(make_hospital())
        doctor.specialities.add(baker.make_recipe("apps.catalog.tests.speciality"))
    baker.make_recipe("apps.content.tests.testimonial", _quantity=2)
    baker.make_recipe("apps.locations.tests.source_country", _quantity=3)
    baker.make_recipe("apps.content.tests.article", _quantity=3)

    # Treatments, exchange rate, hero packages and their accreditations,
    # specialities, cities, hospitals and their accreditations, doctors (with
    # hospitals, their accreditations and specialities), stories, countries, guides.
    with django_assert_num_queries(15):
        client.get(reverse("website:home"))


def test_only_the_medical_opinion_card_is_highlighted(client):
    """Guards cotton flags: an unquoted dark=False quoted by a formatter becomes
    the string "False", which is truthy and darkens every card."""
    content = client.get(reverse("website:home")).content.decode()

    assert content.count("border-brand-950 bg-brand-950") == 1


def test_city_filter_sends_htmx_only_the_hospitals_panel(client):
    chennai = baker.make_recipe("apps.locations.tests.city", slug="chennai")
    in_chennai = make_hospital(city=chennai)
    make_hospital()

    response = client.get(
        reverse("website:home"), {"city": "chennai"}, headers=HTMX_PARTIAL
    )

    templates = [t.name for t in response.templates]
    assert "website/home/hospitals_panel.html" in templates
    assert "base.html" not in templates
    assert list(response.context["hospitals"]) == [in_chennai]
    assert "HX-Request-Type" in response["Vary"]


def test_city_filter_works_without_javascript(client):
    chennai = baker.make_recipe("apps.locations.tests.city", slug="chennai")
    in_chennai = make_hospital(city=chennai)
    make_hospital()

    response = client.get(reverse("website:home"), {"city": "chennai"})

    assert "base.html" in [t.name for t in response.templates]
    assert response.context["selected_city"] == chennai
    assert list(response.context["hospitals"]) == [in_chennai]


def test_history_restore_gets_the_full_page(client):
    make_hospital()

    response = client.get(
        reverse("website:home"),
        headers={"HX-Request": "true", "HX-Request-Type": "full"},
    )

    assert "base.html" in [t.name for t in response.templates]


def test_unknown_city_shows_hospitals_in_every_city(client):
    make_hospital(_quantity=2)

    response = client.get(reverse("website:home"), {"city": "atlantis"})

    assert response.context["selected_city"] is None
    assert len(response.context["hospitals"]) == 2


def test_only_verified_registrations_get_the_badge_and_numbers_stay_private(client):
    baker.make_recipe(
        "apps.providers.tests.doctor",
        medical_registration_number="DMC-12345",
        registration_verified_on=timezone.localdate(),
    )
    baker.make_recipe(
        "apps.providers.tests.doctor", medical_registration_number="DMC-67890"
    )

    content = client.get(reverse("website:home")).content.decode()

    assert content.count("Registration verified") == 1
    assert "DMC-" not in content


def test_patient_stories_and_countries_are_shown(client):
    baker.make_recipe("apps.content.tests.testimonial", quote="Kind and clear.")
    baker.make_recipe(
        "apps.locations.tests.source_country", country="BD", slug="bangladesh"
    )

    content = client.get(reverse("website:home")).content.decode()

    assert "Kind and clear." in content
    assert "/medical-travel-from-bangladesh-to-india/" in content


def test_only_the_first_faq_starts_open(client):
    content = client.get(reverse("website:home")).content.decode()

    details = re.findall(r"<details[^>]*>", content)
    assert len(details) == 5
    assert sum(bool(re.search(r"\sopen\s", tag)) for tag in details) == 1
