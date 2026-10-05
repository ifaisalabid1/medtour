import pytest

from apps.leads.consent import CONSENT_TEXT_VERSION, CONSENT_TEXTS
from apps.leads.forms import EnquiryForm
from apps.leads.models import ConsentPurpose, Enquiry
from apps.leads.services import (
    MAX_ENQUIRIES_PER_IP_PER_HOUR,
    SubmissionContext,
    TooManyEnquiries,
    create_enquiry,
    withdraw_consent,
)

pytestmark = pytest.mark.django_db

CONTEXT = SubmissionContext(
    ip_address="203.0.113.7",
    user_agent="Mozilla/5.0",
    tracking={"utm_source": "google", "landing_page": "/treatments/knee/"},
)


def cleaned(enquiry_data, files=None):
    form = EnquiryForm(enquiry_data, files or {}, remote_ip=CONTEXT.ip_address)
    assert form.is_valid(), form.errors
    return form.cleaned_data


def test_enquiry_is_saved_with_documents_tracking_and_consent(
    enquiry_data, pdf_report, turnstile_passes
):
    enquiry = create_enquiry(
        cleaned_data=cleaned(enquiry_data, {"documents": [pdf_report]}),
        context=CONTEXT,
    )

    assert enquiry.reference.startswith("MT-")
    assert str(enquiry.phone) == "+8801712345678"
    assert enquiry.utm_source == "google"
    assert enquiry.landing_page == "/treatments/knee/"
    assert [d.original_name for d in enquiry.documents.all()] == ["blood-test.pdf"]

    consent = enquiry.consents.get()
    assert consent.purpose == ConsentPurpose.PROCESS_ENQUIRY
    assert consent.consent_text == CONSENT_TEXTS[ConsentPurpose.PROCESS_ENQUIRY]
    assert consent.consent_text_version == CONSENT_TEXT_VERSION
    assert consent.ip_address == "203.0.113.7"


def test_marketing_consent_is_only_recorded_when_given(enquiry_data, turnstile_passes):
    enquiry_data["consent_to_marketing"] = "on"

    enquiry = create_enquiry(cleaned_data=cleaned(enquiry_data), context=CONTEXT)

    assert set(enquiry.consents.values_list("purpose", flat=True)) == {
        ConsentPurpose.PROCESS_ENQUIRY,
        ConsentPurpose.MARKETING,
    }


def test_too_many_enquiries_from_one_ip_are_refused(enquiry_data, turnstile_passes):
    data = cleaned(enquiry_data)
    for _ in range(MAX_ENQUIRIES_PER_IP_PER_HOUR):
        create_enquiry(cleaned_data=data, context=CONTEXT)

    with pytest.raises(TooManyEnquiries):
        create_enquiry(cleaned_data=data, context=CONTEXT)

    other_visitor = SubmissionContext(ip_address="198.51.100.20")
    create_enquiry(cleaned_data=data, context=other_visitor)  # still allowed
    assert Enquiry.objects.count() == MAX_ENQUIRIES_PER_IP_PER_HOUR + 1


def test_overlong_tracking_values_are_cut_not_rejected(enquiry_data, turnstile_passes):
    context = SubmissionContext(tracking={"utm_campaign": "x" * 1000})

    enquiry = create_enquiry(cleaned_data=cleaned(enquiry_data), context=context)

    assert len(enquiry.utm_campaign) == 200


def test_nothing_is_saved_if_a_document_fails_to_store(
    enquiry_data, pdf_report, turnstile_passes, monkeypatch
):
    from apps.leads.models import EnquiryDocument

    def broken_save(*args, **kwargs):
        raise OSError("storage unavailable")

    monkeypatch.setattr(EnquiryDocument, "save", broken_save)

    with pytest.raises(OSError):
        create_enquiry(
            cleaned_data=cleaned(enquiry_data, {"documents": [pdf_report]}),
            context=CONTEXT,
        )

    assert Enquiry.objects.count() == 0


def test_withdrawing_consent_keeps_the_record(enquiry_data, turnstile_passes):
    enquiry = create_enquiry(cleaned_data=cleaned(enquiry_data), context=CONTEXT)

    changed = withdraw_consent(enquiry=enquiry, purpose=ConsentPurpose.PROCESS_ENQUIRY)

    consent = enquiry.consents.get()
    assert changed == 1
    assert consent.withdrawn_at is not None


def test_emails_are_sent_once_the_enquiry_is_committed(
    enquiry_data, turnstile_passes, django_capture_on_commit_callbacks, mailoutbox
):
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        enquiry = create_enquiry(cleaned_data=cleaned(enquiry_data), context=CONTEXT)

    assert len(callbacks) == 2
    assert {tuple(email.to) for email in mailoutbox} == {
        ("rahim@example.com",),
        ("team@medtour.example",),
    }
    assert all(enquiry.reference in email.subject for email in mailoutbox)


def test_no_emails_if_the_enquiry_is_rolled_back(
    enquiry_data,
    pdf_report,
    turnstile_passes,
    monkeypatch,
    django_capture_on_commit_callbacks,
    mailoutbox,
):
    from apps.leads.models import EnquiryDocument

    def broken_save(*args, **kwargs):
        raise OSError("storage unavailable")

    monkeypatch.setattr(EnquiryDocument, "save", broken_save)

    with django_capture_on_commit_callbacks(execute=True), pytest.raises(OSError):
        create_enquiry(
            cleaned_data=cleaned(enquiry_data, {"documents": [pdf_report]}),
            context=CONTEXT,
        )

    assert mailoutbox == []
