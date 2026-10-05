"""Background tasks for leads. Run by `manage.py db_worker`."""

import logging
from datetime import timedelta

from django.tasks import task
from django.utils import timezone

from . import notifications
from .models import Enquiry

logger = logging.getLogger(__name__)

# Retries wait 2, 4, 8 and 16 minutes, so a short email-provider outage
# doesn't lose a patient's confirmation or the team's alert.
MAX_ATTEMPTS = 5


@task(queue_name="emails")
def send_enquiry_received_email(enquiry_id: int, attempt: int = 1) -> None:
    enquiry = _load_enquiry(enquiry_id)
    if enquiry is None:
        return
    try:
        notifications.send_enquiry_received(enquiry)
    except Exception as error:
        _retry_later(send_enquiry_received_email, enquiry_id, attempt, error)


@task(queue_name="emails")
def send_new_enquiry_alert_email(enquiry_id: int, attempt: int = 1) -> None:
    enquiry = _load_enquiry(enquiry_id)
    if enquiry is None:
        return
    try:
        notifications.send_new_enquiry_alert(enquiry)
    except Exception as error:
        _retry_later(send_new_enquiry_alert_email, enquiry_id, attempt, error)


def _load_enquiry(enquiry_id: int) -> Enquiry | None:
    # The enquiry may be gone (e.g. deleted after an erasure request) by the
    # time the worker runs; there's then nothing to send.
    return Enquiry.objects.select_related("treatment").filter(pk=enquiry_id).first()


def _retry_later(email_task, enquiry_id: int, attempt: int, error: Exception) -> None:
    if attempt >= MAX_ATTEMPTS:
        # Give up: the task is marked failed, with its traceback, in the admin.
        raise error
    delay = timedelta(minutes=2**attempt)
    logger.warning(
        "%s for enquiry %s failed (attempt %s); retrying in %s",
        email_task.name,
        enquiry_id,
        attempt,
        delay,
        exc_info=error,
    )
    # run_after must be a datetime: Django 6.1 rejects a timedelta here.
    email_task.using(run_after=timezone.now() + delay).enqueue(
        enquiry_id, attempt=attempt + 1
    )
