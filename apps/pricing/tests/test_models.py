import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from apps.pricing.models import TreatmentPackage

pytestmark = pytest.mark.django_db


@pytest.fixture
def treatment_and_hospital():
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    hospital = baker.make_recipe("apps.providers.tests.hospital")
    hospital.specialities.add(treatment.speciality)
    return treatment, hospital


def test_a_valid_package_passes_validation(treatment_and_hospital):
    treatment, hospital = treatment_and_hospital
    package = TreatmentPackage(
        treatment=treatment, hospital=hospital, price_min_inr=250_000
    )

    package.full_clean()  # must not raise


def test_upper_price_cannot_be_below_starting_price(treatment_and_hospital):
    treatment, hospital = treatment_and_hospital
    package = TreatmentPackage(
        treatment=treatment,
        hospital=hospital,
        price_min_inr=300_000,
        price_max_inr=200_000,
    )

    with pytest.raises(ValidationError, match="cannot be lower"):
        package.full_clean()


def test_one_package_per_treatment_and_hospital(treatment_and_hospital):
    treatment, hospital = treatment_and_hospital
    TreatmentPackage.objects.create(
        treatment=treatment, hospital=hospital, price_min_inr=250_000
    )
    duplicate = TreatmentPackage(
        treatment=treatment, hospital=hospital, price_min_inr=260_000
    )

    with pytest.raises(ValidationError, match="already has a package"):
        duplicate.full_clean()


def test_hospital_must_offer_the_treatments_speciality():
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    hospital = baker.make_recipe("apps.providers.tests.hospital")
    package = TreatmentPackage(
        treatment=treatment, hospital=hospital, price_min_inr=250_000
    )

    with pytest.raises(ValidationError) as exc:
        package.full_clean()

    assert "hospital" in exc.value.message_dict


def test_inclusions_are_split_into_lines_ignoring_blanks():
    package = TreatmentPackage(inclusions="Surgery\n\n  5 nights in hospital  \n")

    assert package.inclusion_list == ["Surgery", "5 nights in hospital"]
    assert package.exclusion_list == []


def test_upper_price_falls_back_to_the_starting_price():
    single_price = TreatmentPackage(price_min_inr=100)
    price_range = TreatmentPackage(price_min_inr=100, price_max_inr=150)

    assert single_price.price_upper_inr == 100
    assert price_range.price_upper_inr == 150
