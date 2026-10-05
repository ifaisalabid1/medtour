import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:catalog_speciality_changelist",
        "admin:catalog_speciality_add",
        "admin:catalog_treatment_changelist",
        "admin:catalog_treatment_add",
        "admin:catalog_condition_changelist",
        "admin:catalog_condition_add",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    treatment = baker.make_recipe("apps.catalog.tests.treatment")
    condition = baker.make_recipe("apps.catalog.tests.condition")
    condition.treatments.add(treatment)

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200
