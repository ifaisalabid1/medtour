import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:providers_accreditation_changelist",
        "admin:providers_accreditation_add",
        "admin:providers_hospital_changelist",
        "admin:providers_hospital_add",
        "admin:providers_doctor_changelist",
        "admin:providers_doctor_add",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    hospital = baker.make_recipe("apps.providers.tests.hospital")
    doctor = baker.make_recipe("apps.providers.tests.doctor")
    doctor.hospitals.add(hospital)
    baker.make_recipe("apps.providers.tests.accreditation")

    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200


def test_hospital_change_page_renders_with_accreditation_inline(admin_client):
    hospital = baker.make_recipe("apps.providers.tests.hospital")
    hospital.accreditations.add(baker.make_recipe("apps.providers.tests.accreditation"))

    response = admin_client.get(
        reverse("admin:providers_hospital_change", args=[hospital.pk])
    )

    assert response.status_code == 200
