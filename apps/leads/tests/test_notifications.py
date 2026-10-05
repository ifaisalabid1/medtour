import pytest
from django.core import mail
from model_bakery import baker

from apps.leads.models import Enquiry
from apps.leads.notifications import send_enquiry_received, send_new_enquiry_alert

pytestmark = pytest.mark.django_db


@pytest.fixture
def enquiry():
    return baker.make(
        Enquiry,
        full_name="Siobhan O'Brien & Family",
        email="patient@example.com",
        phone="+8801712345678",
        country="BD",
        prefers_whatsapp=True,
        message="Confidential: biopsy shows a tumour.",
    )


def test_patient_confirmation(enquiry):
    send_enquiry_received(enquiry)

    [email] = mail.outbox
    assert email.to == ["patient@example.com"]
    assert enquiry.reference in email.subject
    assert enquiry.reference in email.body
    assert "on WhatsApp at +8801712345678" in email.body
    # Plain-text email: names must not be HTML-escaped (&amp; or &#x27;).
    assert "Dear Siobhan O'Brien & Family," in email.body


def test_team_alert_links_to_the_case_without_medical_details(enquiry):
    send_new_enquiry_alert(enquiry)

    [email] = mail.outbox
    assert email.to == ["team@medtour.example"]
    assert "Bangladesh" in email.subject
    assert (
        f"https://medtour.example/admin/leads/enquiry/{enquiry.pk}/change/"
        in email.body
    )
    assert "tumour" not in email.body


def test_no_team_alert_when_no_inbox_is_configured(enquiry, settings):
    settings.ENQUIRY_ALERT_EMAILS = []

    send_new_enquiry_alert(enquiry)

    assert mail.outbox == []
