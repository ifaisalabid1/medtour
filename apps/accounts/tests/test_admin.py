import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:accounts_user_changelist",
        "admin:accounts_user_add",
        "admin:auth_group_changelist",
    ],
)
def test_admin_pages_render(admin_client, url_name):
    response = admin_client.get(reverse(url_name))

    assert response.status_code == 200
