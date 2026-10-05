import pytest
from model_bakery import baker

from apps.catalog.selectors import published_treatments, search_treatments

pytestmark = pytest.mark.django_db


def make_treatment(**fields):
    return baker.make_recipe("apps.catalog.tests.treatment", **fields)


def test_published_treatments_hides_treatments_of_unpublished_specialities():
    hidden_speciality = baker.make_recipe(
        "apps.catalog.tests.speciality", is_published=False
    )
    visible = make_treatment()
    make_treatment(speciality=hidden_speciality)

    assert list(published_treatments()) == [visible]


def test_search_matches_partial_words():
    knee = make_treatment(name="Total Knee Replacement")

    assert list(search_treatments("kne replac")) == [knee]


def test_search_matches_alternative_names():
    knee = make_treatment(
        name="Total Knee Replacement", also_known_as="TKR, knee arthroplasty"
    )

    assert list(search_treatments("tkr")) == [knee]


def test_search_matches_through_linked_conditions():
    knee = make_treatment(name="Total Knee Replacement")
    condition = baker.make_recipe(
        "apps.catalog.tests.condition", name="Osteoarthritis", also_known_as="arthritis"
    )
    condition.treatments.add(knee)

    assert list(search_treatments("arthritis")) == [knee]


def test_search_ranks_name_matches_above_summary_matches():
    summary_match = make_treatment(
        name="Hip Replacement", summary="Often compared with knee surgery"
    )
    name_match = make_treatment(name="Knee Arthroscopy")

    assert list(search_treatments("knee")) == [name_match, summary_match]


def test_search_excludes_unpublished_treatments():
    make_treatment(name="Knee Arthroscopy", is_published=False)

    assert list(search_treatments("knee")) == []


def test_search_reflects_edits_immediately():
    treatment = make_treatment(name="Knee Arthroscopy")
    treatment.name = "Knee Keyhole Surgery"
    treatment.save()

    assert list(search_treatments("keyhole")) == [treatment]


def test_search_with_nothing_searchable_returns_nothing():
    make_treatment(name="Knee Arthroscopy")

    assert list(search_treatments("&&")) == []
