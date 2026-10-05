from dataclasses import dataclass, field
from datetime import timedelta
from functools import partial

from django.db import transaction
from django.utils import timezone

from .consent import CONSENT_TEXT_VERSION, CONSENT_TEXTS
from .models import ConsentPurpose, ConsentRecord, Enquiry, EnquiryDocument
from .tasks import send_enquiry_received_email, send_new_enquiry_alert_email

# A real patient rarely sends more than one or two enquiries an hour.
MAX_ENQUIRIES_PER_IP_PER_HOUR = 5

TRACKING_FIELDS = (
    "landing_page",
    "referrer",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
)


class TooManyEnquiries(Exception):
    pass


@dataclass(frozen=True)
class SubmissionContext:
    """Facts about the HTTP request, collected by the view."""

    ip_address: str | None = None
    user_agent: str = ""
    tracking: dict[str, str] = field(default_factory=dict)


def create_enquiry(*, cleaned_data: dict, context: SubmissionContext) -> Enquiry:
    """Save a validated enquiry, its documents and the patient's consent.

    Everything is written in one transaction: an enquiry is never stored
    without its consent record, or with only some of its documents.
    """
    if _too_many_recent_enquiries(context.ip_address):
        raise TooManyEnquiries

    # Tracking values come from the URL, so anyone can send anything: cut
    # them to the column length instead of failing the patient's enquiry.
    tracking = {
        name: str(context.tracking.get(name, ""))[
            : Enquiry._meta.get_field(name).max_length
        ]
        for name in TRACKING_FIELDS
    }

    with transaction.atomic():
        enquiry = Enquiry.objects.create(
            full_name=cleaned_data["full_name"],
            email=cleaned_data["email"],
            phone=cleaned_data["phone"],
            prefers_whatsapp=cleaned_data["prefers_whatsapp"],
            country=cleaned_data["country"],
            patient_age=cleaned_data.get("patient_age"),
            treatment=cleaned_data.get("treatment"),
            message=cleaned_data["message"],
            **tracking,
        )
        for uploaded in cleaned_data.get("documents", []):
            EnquiryDocument.objects.create(
                enquiry=enquiry, file=uploaded, original_name=uploaded.name[:255]
            )
        _record_consent(enquiry, ConsentPurpose.PROCESS_ENQUIRY, context)
        if cleaned_data.get("consent_to_marketing"):
            _record_consent(enquiry, ConsentPurpose.MARKETING, context)

        # Queue the emails only once the enquiry is committed; otherwise the
        # worker could run before the data exists, or email about an enquiry
        # that was rolled back.
        transaction.on_commit(partial(send_enquiry_received_email.enqueue, enquiry.pk))
        transaction.on_commit(partial(send_new_enquiry_alert_email.enqueue, enquiry.pk))

    return enquiry


def _too_many_recent_enquiries(ip_address: str | None) -> bool:
    if not ip_address:
        return False
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent = ConsentRecord.objects.filter(
        purpose=ConsentPurpose.PROCESS_ENQUIRY,
        ip_address=ip_address,
        granted_at__gte=one_hour_ago,
    ).count()
    return recent >= MAX_ENQUIRIES_PER_IP_PER_HOUR


def _record_consent(
    enquiry: Enquiry, purpose: ConsentPurpose, context: SubmissionContext
) -> None:
    ConsentRecord.objects.create(
        enquiry=enquiry,
        purpose=purpose,
        consent_text_version=CONSENT_TEXT_VERSION,
        consent_text=CONSENT_TEXTS[purpose],
        ip_address=context.ip_address,
        user_agent=context.user_agent[:300],
    )


def withdraw_consent(*, enquiry: Enquiry, purpose: ConsentPurpose) -> int:
    """Mark a patient's consent as withdrawn. Returns how many records changed."""
    return enquiry.consents.filter(purpose=purpose, withdrawn_at__isnull=True).update(
        withdrawn_at=timezone.now()
    )
