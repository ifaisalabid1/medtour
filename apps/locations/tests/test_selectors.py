import pytest
from model_bakery import baker

from apps.locations.selectors import published_cities, published_source_countries

pytestmark = pytest.mark.django_db


def test_published_cities_excludes_unpublished():
    visible = baker.make_recipe("apps.locations.tests.city")
    baker.make_recipe("apps.locations.tests.city", is_published=False)

    assert list(published_cities()) == [visible]


def test_published_source_countries_excludes_unpublished():
    visible = baker.make_recipe("apps.locations.tests.source_country")
    baker.make_recipe("apps.locations.tests.source_country", is_published=False)

    assert list(published_source_countries()) == [visible]
