from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse
from model_bakery import baker

from apps.pricing.models import ExchangeRate

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:pricing_treatmentpackage_changelist",
        "admin:pricing_treatmentpackage_add",
        "admin:pricing_exchangerate_changelist",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    baker.make_recipe("apps.pricing.tests.package")
    ExchangeRate.objects.create(
        currency="USD", inr_per_unit=Decimal("96.32"), rate_date=date(2026, 10, 2)
    )

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200
