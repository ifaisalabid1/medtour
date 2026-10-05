import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.datastructures import MultiValueDict
from model_bakery import baker

from apps.leads import forms
from apps.leads.forms import EnquiryForm

pytestmark = pytest.mark.django_db


def make_form(data, files=None, remote_ip="203.0.113.7"):
    return EnquiryForm(data, MultiValueDict(files or {}), remote_ip=remote_ip)


def test_a_complete_enquiry_is_valid(enquiry_data, pdf_report, turnstile_passes):
    form = make_form(enquiry_data, {"documents": [pdf_report]})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["documents"] == [pdf_report]
    assert turnstile_passes == [("token-from-the-widget", "203.0.113.7")]


def test_consent_to_process_is_required(enquiry_data, turnstile_passes):
    del enquiry_data["consent_to_process"]

    form = make_form(enquiry_data)

    assert "consent_to_process" in form.errors


def test_files_that_are_not_pdfs_or_images_are_rejected(enquiry_data, turnstile_passes):
    renamed = SimpleUploadedFile("report.pdf", b"MZ executable")

    form = make_form(enquiry_data, {"documents": [renamed]})

    assert "documents" in form.errors


def test_at_most_five_documents(enquiry_data, turnstile_passes):
    files = [SimpleUploadedFile(f"r{i}.pdf", b"%PDF-1.7") for i in range(6)]

    form = make_form(enquiry_data, {"documents": files})

    assert "documents" in form.errors


def test_failed_turnstile_check_blocks_the_form(enquiry_data, monkeypatch):
    monkeypatch.setattr(forms, "verify_turnstile", lambda token, ip: False)

    form = make_form(enquiry_data)

    assert not form.is_valid()
    assert "not a robot" in str(form.non_field_errors())


def test_turnstile_is_not_checked_while_other_fields_have_errors(
    enquiry_data, turnstile_passes
):
    enquiry_data["email"] = "not-an-email"

    make_form(enquiry_data).is_valid()

    assert turnstile_passes == []


def test_only_published_treatments_can_be_chosen(enquiry_data, turnstile_passes):
    hidden = baker.make_recipe("apps.catalog.tests.treatment", is_published=False)
    enquiry_data["treatment"] = str(hidden.pk)

    form = make_form(enquiry_data)

    assert "treatment" in form.errors
