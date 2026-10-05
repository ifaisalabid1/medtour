import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from apps.locations.models import City, SourceCountry

pytestmark = pytest.mark.django_db


def test_city_name_is_unique_within_a_state_ignoring_case():
    baker.make_recipe("apps.locations.tests.city", name="Mumbai", state="Maharashtra")
    duplicate = City(name="MUMBAI", slug="mumbai-2", state="Maharashtra")

    with pytest.raises(ValidationError, match="already exists in this state"):
        duplicate.full_clean()


def test_same_city_name_is_allowed_in_different_states():
    baker.make_recipe(
        "apps.locations.tests.city", name="Aurangabad", state="Maharashtra"
    )
    other = City(name="Aurangabad", slug="aurangabad-bihar", state="Bihar")

    other.full_clean()  # must not raise


def test_source_country_slug_is_generated_from_country_name():
    country = SourceCountry.objects.create(country="BD")

    assert country.slug == "bangladesh"
    assert str(country) == "Bangladesh"


def test_source_country_keeps_a_custom_slug():
    country = SourceCountry.objects.create(country="AE", slug="uae")

    assert country.slug == "uae"


def test_city_state_must_be_a_real_indian_state():
    city = City(name="Chennai", slug="chennai", state="Tamilnadu")

    with pytest.raises(ValidationError) as exc:
        city.full_clean()

    assert "state" in exc.value.message_dict
