from datetime import timedelta

import pytest
from django.core import mail
from django.tasks import default_task_backend
from django.utils import timezone
from model_bakery import baker

from apps.leads import notifications
from apps.leads.models import Enquiry
from apps.leads.tasks import (
    MAX_ATTEMPTS,
    send_enquiry_received_email,
    send_new_enquiry_alert_email,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def enquiry():
    return baker.make(
        Enquiry, email="patient@example.com", phone="+8801712345678", country="BD"
    )


@pytest.fixture
def dummy_task_backend(settings):
    """Store enqueued tasks instead of running them, so retries can be inspected."""
    settings.TASKS = {
        "default": {
            "BACKEND": "django.tasks.backends.dummy.DummyBackend",
            "QUEUES": ["default", "emails"],
        }
    }
    return default_task_backend


def test_tasks_send_their_emails(enquiry):
    send_enquiry_received_email.call(enquiry.pk)
    send_new_enquiry_alert_email.call(enquiry.pk)

    assert [email.to for email in mail.outbox] == [
        ["patient@example.com"],
        ["team@medtour.example"],
    ]


def test_nothing_is_sent_for_a_deleted_enquiry(enquiry):
    enquiry_id = enquiry.pk
    enquiry.delete()

    send_enquiry_received_email.call(enquiry_id)

    assert mail.outbox == []


def test_a_failed_send_is_retried_later(enquiry, dummy_task_backend, monkeypatch):
    def provider_down(enquiry):
        raise ConnectionError("email provider unavailable")

    monkeypatch.setattr(notifications, "send_enquiry_received", provider_down)

    send_enquiry_received_email.call(enquiry.pk)

    [retry] = dummy_task_backend.results
    assert retry.args == [enquiry.pk]
    assert retry.kwargs == {"attempt": 2}
    assert retry.task.run_after > timezone.now() + timedelta(minutes=1)


def test_the_last_attempt_fails_loudly(enquiry, dummy_task_backend, monkeypatch):
    def provider_down(enquiry):
        raise ConnectionError("email provider unavailable")

    monkeypatch.setattr(notifications, "send_enquiry_received", provider_down)

    with pytest.raises(ConnectionError):
        send_enquiry_received_email.call(enquiry.pk, attempt=MAX_ATTEMPTS)

    assert dummy_task_backend.results == []
