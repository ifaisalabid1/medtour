import pytest
from axes.models import AccessAttempt
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db

PASSWORD = "a-long-test-password"


@pytest.fixture
def staff(django_user_model):
    return django_user_model.objects.create_user(
        email="manager@example.com", password=PASSWORD, is_staff=True
    )


def log_in(client, email, password):
    return client.post(
        reverse("admin:login"), {"username": email, "password": password}
    )


# --- Content Security Policy ---------------------------------------------------


def test_public_pages_get_the_strict_policy(client):
    treatment = baker.make_recipe("apps.catalog.tests.treatment")

    policy = client.get(treatment.get_absolute_url())["Content-Security-Policy"]

    # A nonce is only added once a template uses {{ csp_nonce }}.
    assert "script-src 'self'" in policy
    assert "unsafe" not in policy
    assert "frame-ancestors 'none'" in policy


def test_admin_pages_get_the_admin_policy(admin_client):
    policy = admin_client.get(reverse("admin:index"))["Content-Security-Policy"]

    assert "script-src 'self' 'unsafe-inline' 'unsafe-eval'" in policy
    assert "nonce-" not in policy


# --- Admin login -----------------------------------------------------------------


def test_logging_in_directly_lands_on_the_admin(client, staff):
    response = log_in(client, staff.email, PASSWORD)

    assert response.status_code == 302
    assert response["Location"] == reverse("admin:index")


def test_repeated_failed_logins_lock_the_account(client, staff):
    for _ in range(5):
        log_in(client, staff.email, "wrong-password")

    assert AccessAttempt.objects.get().username == staff.email

    # Even the right password is refused while locked out.
    response = log_in(client, staff.email, PASSWORD)

    assert response.status_code == 429


def test_a_lockout_does_not_affect_other_staff(client, staff, django_user_model):
    colleague = django_user_model.objects.create_user(
        email="colleague@example.com", password=PASSWORD, is_staff=True
    )
    for _ in range(5):
        log_in(client, staff.email, "wrong-password")

    response = log_in(client, colleague.email, PASSWORD)

    assert response.status_code == 302


# --- Health check ----------------------------------------------------------------


def test_health_check_reports_database_and_storages(client):
    response = client.get("/health/?format=json")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 3  # database, public storage, private storage
    assert set(results.values()) == {"OK"}
