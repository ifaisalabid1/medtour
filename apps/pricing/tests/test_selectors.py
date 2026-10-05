from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from model_bakery import baker

from apps.catalog.models import Treatment
from apps.pricing.models import ExchangeRate
from apps.pricing.selectors import (
    CostSummary,
    cost_summary,
    current_inr_per_unit,
    packages_for_treatment,
    with_starting_price,
)

pytestmark = pytest.mark.django_db


def make_package(treatment, **fields):
    return baker.make_recipe(
        "apps.pricing.tests.package", treatment=treatment, **fields
    )


@pytest.fixture
def treatment():
    return baker.make_recipe("apps.catalog.tests.treatment")


def test_packages_are_listed_cheapest_first(treatment):
    expensive = make_package(treatment, price_min_inr=400_000)
    cheap = make_package(treatment, price_min_inr=200_000)

    assert list(packages_for_treatment(treatment)) == [cheap, expensive]


def test_packages_of_hidden_hospitals_or_cities_are_excluded(treatment):
    visible = make_package(treatment)
    make_package(treatment, is_published=False)
    make_package(
        treatment,
        hospital=baker.make_recipe("apps.providers.tests.hospital", is_published=False),
    )
    hidden_city = baker.make_recipe("apps.locations.tests.city", is_published=False)
    make_package(
        treatment,
        hospital=baker.make_recipe("apps.providers.tests.hospital", city=hidden_city),
    )

    assert list(packages_for_treatment(treatment)) == [visible]


def test_cost_summary_spans_all_public_packages(treatment):
    make_package(treatment, price_min_inr=200_000, price_max_inr=300_000)
    make_package(treatment, price_min_inr=350_000)  # single price
    make_package(treatment, price_min_inr=100_000, is_published=False)

    assert cost_summary(treatment) == CostSummary(
        min_inr=200_000, max_inr=350_000, hospital_count=2
    )


def test_cost_summary_is_none_without_public_packages(treatment):
    make_package(treatment, is_published=False)

    assert cost_summary(treatment) is None


def test_with_starting_price_annotates_the_cheapest_public_price(treatment):
    make_package(treatment, price_min_inr=300_000)
    make_package(treatment, price_min_inr=250_000)
    make_package(treatment, price_min_inr=100_000, is_published=False)
    unpriced = baker.make_recipe("apps.catalog.tests.treatment")

    prices = dict(
        with_starting_price(Treatment.objects.all()).values_list(
            "pk", "starting_price_inr"
        )
    )

    assert prices == {treatment.pk: 250_000, unpriced.pk: None}


def test_current_rate_is_returned_while_fresh():
    ExchangeRate.objects.create(
        currency="USD", inr_per_unit=Decimal("96.32"), rate_date=timezone.localdate()
    )

    assert current_inr_per_unit("USD") == Decimal("96.32")


def test_stale_or_missing_rates_are_not_used():
    ExchangeRate.objects.create(
        currency="USD",
        inr_per_unit=Decimal("96.32"),
        rate_date=timezone.localdate() - timedelta(days=8),
    )

    assert current_inr_per_unit("USD") is None
    assert current_inr_per_unit("EUR") is None
