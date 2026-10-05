import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.leads import forms


@pytest.fixture
def turnstile_passes(monkeypatch):
    """Pretend Cloudflare accepted the Turnstile token."""
    calls = []

    def fake_verify(token, remote_ip):
        calls.append((token, remote_ip))
        return True

    monkeypatch.setattr(forms, "verify_turnstile", fake_verify)
    return calls


@pytest.fixture
def pdf_report():
    return SimpleUploadedFile(
        "blood-test.pdf", b"%PDF-1.7 report", content_type="application/pdf"
    )


@pytest.fixture
def enquiry_data():
    return {
        "full_name": "Rahim Uddin",
        "email": "rahim@example.com",
        "phone": "+8801712345678",
        "prefers_whatsapp": "on",
        "country": "BD",
        "patient_age": "58",
        "message": "My father needs a knee replacement. Reports attached.",
        "consent_to_process": "on",
        "cf-turnstile-response": "token-from-the-widget",
    }
