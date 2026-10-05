from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from apps.providers.models import HospitalAccreditation
from apps.providers.selectors import (
    published_doctors,
    published_hospitals,
    search_doctors,
    search_hospitals,
)

pytestmark = pytest.mark.django_db


def make_hospital(**fields):
    return baker.make_recipe("apps.providers.tests.hospital", **fields)


def make_doctor(**fields):
    return baker.make_recipe("apps.providers.tests.doctor", **fields)


def test_published_hospitals_hides_hospitals_in_unpublished_cities():
    hidden_city = baker.make_recipe("apps.locations.tests.city", is_published=False)
    visible = make_hospital()
    make_hospital(city=hidden_city)

    assert list(published_hospitals()) == [visible]


def test_only_unexpired_accreditations_are_shown():
    hospital = make_hospital()
    nabh, jci, iso = baker.make_recipe(
        "apps.providers.tests.accreditation", _quantity=3
    )
    today = timezone.localdate()
    HospitalAccreditation.objects.create(
        hospital=hospital, accreditation=nabh, valid_until=today
    )
    HospitalAccreditation.objects.create(
        hospital=hospital, accreditation=jci, valid_until=today - timedelta(days=1)
    )
    HospitalAccreditation.objects.create(hospital=hospital, accreditation=iso)

    shown = published_hospitals().get().current_accreditations

    assert {record.accreditation for record in shown} == {nabh, iso}


def test_doctor_lists_only_public_hospitals_and_specialities():
    public_hospital = make_hospital()
    hidden_hospital = make_hospital(is_published=False)
    public_speciality = baker.make_recipe("apps.catalog.tests.speciality")
    hidden_speciality = baker.make_recipe(
        "apps.catalog.tests.speciality", is_published=False
    )
    doctor = make_doctor()
    doctor.hospitals.add(public_hospital, hidden_hospital)
    doctor.specialities.add(public_speciality, hidden_speciality)

    loaded = published_doctors().get()

    assert loaded.public_hospitals == [public_hospital]
    assert loaded.public_specialities == [public_speciality]


def test_doctor_listing_uses_a_fixed_number_of_queries(django_assert_num_queries):
    for _ in range(3):
        doctor = make_doctor()
        doctor.hospitals.add(make_hospital())
        doctor.specialities.add(baker.make_recipe("apps.catalog.tests.speciality"))

    # doctors + hospitals (with cities) + accreditations + specialities,
    # however many doctors there are.
    with django_assert_num_queries(4):
        for doctor in published_doctors():
            for hospital in doctor.public_hospitals:
                str(hospital.city)
                list(hospital.current_accreditations)
            list(doctor.public_specialities)


def test_search_hospitals_by_partial_name_and_alternative_name():
    medanta = make_hospital(
        name="Medanta The Medicity", also_known_as="Medanta Gurugram"
    )
    make_hospital(name="Fortis Memorial Research Institute")

    assert list(search_hospitals("medan")) == [medanta]
    assert list(search_hospitals("gurugram")) == [medanta]


def test_search_hospitals_excludes_unpublished():
    make_hospital(name="Medanta The Medicity", is_published=False)

    assert list(search_hospitals("medanta")) == []


def test_search_doctors_ranks_name_above_designation():
    designation_match = make_doctor(name="Asha Rao", designation="Head of Cardiology")
    name_match = make_doctor(name="Cardio Kumar")

    assert list(search_doctors("cardio")) == [name_match, designation_match]


def test_search_with_nothing_searchable_returns_nothing():
    make_hospital(name="Medanta")
    make_doctor(name="Naresh Trehan")

    assert list(search_hospitals("!!")) == []
    assert list(search_doctors("!!")) == []
