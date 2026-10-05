"""Emails about enquiries. Called from background tasks, never from requests."""

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from .models import Enquiry


def send_enquiry_received(enquiry: Enquiry) -> None:
    """Confirm to the patient that their enquiry arrived."""
    EmailMessage(
        subject=f"We've received your enquiry {enquiry.reference}",
        body=render_to_string(
            "leads/emails/enquiry_received.txt", {"enquiry": enquiry}
        ),
        to=[enquiry.email],
    ).send()


def send_new_enquiry_alert(enquiry: Enquiry) -> None:
    """Tell the team a new enquiry is waiting.

    Contains a link to the case, not the patient's medical details: email is
    a less secure channel than the admin, so health data stays out of it.
    """
    if not settings.ENQUIRY_ALERT_EMAILS:
        return
    admin_path = reverse("admin:leads_enquiry_change", args=[enquiry.pk])
    EmailMessage(
        subject=f"New enquiry {enquiry.reference} from {enquiry.country.name}",
        body=render_to_string(
            "leads/emails/new_enquiry_alert.txt",
            {
                "enquiry": enquiry,
                "document_count": enquiry.documents.count(),
                "admin_url": f"{settings.SITE_URL}{admin_path}",
            },
        ),
        to=settings.ENQUIRY_ALERT_EMAILS,
    ).send()
