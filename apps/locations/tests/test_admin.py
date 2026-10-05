import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:locations_city_changelist",
        "admin:locations_city_add",
        "admin:locations_sourcecountry_changelist",
        "admin:locations_sourcecountry_add",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    # Rows exist so the list pages render real columns, not just an empty table.
    baker.make_recipe("apps.locations.tests.city")
    baker.make_recipe("apps.locations.tests.source_country")

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200
