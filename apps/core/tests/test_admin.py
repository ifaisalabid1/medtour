import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_task_results_admin_renders(admin_client):
    url = reverse("admin:django_tasks_database_dbtaskresult_changelist")

    assert admin_client.get(url).status_code == 200
