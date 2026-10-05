import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from apps.catalog.models import Speciality

pytestmark = pytest.mark.django_db


def test_speciality_name_is_unique_ignoring_case():
    baker.make_recipe("apps.catalog.tests.speciality", name="Cardiology")
    duplicate = Speciality(name="CARDIOLOGY", slug="cardiology-2")

    with pytest.raises(ValidationError, match="already exists"):
        duplicate.full_clean()


def test_stay_in_india_cannot_be_shorter_than_hospital_stay():
    treatment = baker.prepare_recipe(
        "apps.catalog.tests.treatment",
        hospital_stay_days=5,
        stay_in_india_days=3,
        _save_related=True,
    )

    with pytest.raises(ValidationError, match="cannot be shorter"):
        treatment.full_clean()
