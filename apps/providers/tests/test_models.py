import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from model_bakery import baker

from apps.providers.models import Doctor, Hospital

pytestmark = pytest.mark.django_db


def test_hospital_name_is_unique_within_a_city_ignoring_case():
    existing = baker.make_recipe(
        "apps.providers.tests.hospital", name="Apollo Hospitals"
    )
    duplicate = Hospital(name="APOLLO HOSPITALS", slug="apollo-2", city=existing.city)

    with pytest.raises(ValidationError, match="already exists in this city"):
        duplicate.full_clean()


def test_same_hospital_name_is_allowed_in_another_city():
    baker.make_recipe("apps.providers.tests.hospital", name="Apollo Hospitals")
    other_city = baker.make_recipe("apps.locations.tests.city")
    branch = Hospital(name="Apollo Hospitals", slug="apollo-chennai", city=other_city)

    branch.full_clean()  # must not raise


def test_year_established_cannot_be_in_the_future():
    hospital = baker.prepare_recipe(
        "apps.providers.tests.hospital",
        established_year=timezone.localdate().year + 1,
        _save_related=True,
    )

    with pytest.raises(ValidationError) as exc:
        hospital.full_clean()

    assert "established_year" in exc.value.message_dict


def test_years_of_experience_is_calculated_from_practising_since():
    doctor = Doctor(practising_since=timezone.localdate().year - 25)

    assert doctor.years_of_experience == 25


def test_years_of_experience_is_none_when_unknown():
    assert Doctor().years_of_experience is None


def test_doctor_str_adds_the_title():
    assert str(Doctor(name="Naresh Trehan")) == "Dr. Naresh Trehan"


def test_a_registration_cannot_be_verified_without_its_number():
    doctor = baker.make_recipe("apps.providers.tests.doctor")
    doctor.registration_verified_on = timezone.localdate()

    with pytest.raises(IntegrityError):
        doctor.save()
