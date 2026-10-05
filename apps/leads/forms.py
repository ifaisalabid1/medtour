from django import forms
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.formfields import PhoneNumberField

from apps.catalog.selectors import published_treatments
from apps.core.validators import (
    validate_document_content,
    validate_document_extension,
    validate_document_size,
)

from .turnstile import verify_turnstile

MAX_DOCUMENTS = 5
TURNSTILE_FIELD = "cf-turnstile-response"


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A file input that accepts several files (pattern from the Django docs)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, list | tuple):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)] if data else []


class EnquiryForm(forms.Form):
    """The public enquiry form. Validates input; saving is the service's job."""

    full_name = forms.CharField(label=_("Full name"), max_length=150)
    email = forms.EmailField(label=_("Email"))
    phone = PhoneNumberField(
        label=_("Phone"),
        help_text=_("Include your country code, e.g. +880 1712 345678."),
    )
    prefers_whatsapp = forms.BooleanField(
        label=_("Contact me on WhatsApp"), required=False, initial=True
    )
    country = CountryField().formfield(label=_("Country"))
    patient_age = forms.IntegerField(
        label=_("Patient's age"), min_value=0, max_value=120, required=False
    )
    treatment = forms.ModelChoiceField(
        label=_("Treatment"),
        queryset=published_treatments(),
        required=False,
        empty_label=_("Not sure yet"),
    )
    message = forms.CharField(
        label=_("Tell us about the medical condition"),
        widget=forms.Textarea,
        max_length=5000,
    )
    documents = MultipleFileField(
        label=_("Medical reports (optional)"),
        required=False,
        validators=[
            validate_document_extension,
            validate_document_size,
            validate_document_content,
        ],
        help_text=_("Up to 5 files: PDF, JPG or PNG, 10 MB each."),
    )
    consent_to_process = forms.BooleanField(required=True)
    consent_to_marketing = forms.BooleanField(required=False)

    def __init__(self, *args, remote_ip: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.remote_ip = remote_ip

    def clean_documents(self):
        documents = self.cleaned_data["documents"]
        if len(documents) > MAX_DOCUMENTS:
            raise forms.ValidationError(
                _("Upload at most %(max)s files."), params={"max": MAX_DOCUMENTS}
            )
        return documents

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            # Fix the visible errors first; a Turnstile token can only be
            # checked once, so don't spend it on a form that will be re-shown.
            return cleaned_data
        token = self.data.get(TURNSTILE_FIELD, "")
        if not verify_turnstile(token, self.remote_ip):
            raise forms.ValidationError(
                _("We couldn't confirm you're not a robot. Please try again."),
                code="turnstile_failed",
            )
        return cleaned_data
