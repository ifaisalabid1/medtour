import secrets

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from simple_history.models import HistoricalRecords

from apps.catalog.models import Treatment
from apps.core.models import TimeStampedModel
from apps.core.storage import private_storage
from apps.core.uploads import unique_upload_path
from apps.providers.models import Doctor, Hospital

# No 0/O or 1/I, so references are easy to read out over the phone.
REFERENCE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_reference() -> str:
    """A short public reference such as "MT-7KQ2X9PD".

    Patients quote this on calls and WhatsApp. It's random, so it reveals
    nothing about how many enquiries the business receives.
    """
    return "MT-" + "".join(secrets.choice(REFERENCE_ALPHABET) for _ in range(8))


def enquiry_document_path(instance, filename):
    return unique_upload_path("enquiries", filename)


class EnquiryStatus(models.TextChoices):
    NEW = "new", _("New")
    CONTACTED = "contacted", _("Contacted")
    QUOTE_SENT = "quote_sent", _("Quote sent")
    TRAVEL_CONFIRMED = "travel_confirmed", _("Travel confirmed")
    TREATED = "treated", _("Treated")
    LOST = "lost", _("Lost")


class Enquiry(TimeStampedModel):
    """A patient's request for help: the start of every case."""

    reference = models.CharField(
        _("reference"),
        max_length=11,
        unique=True,
        default=generate_reference,
        editable=False,
    )

    # Who the patient is.
    full_name = models.CharField(_("full name"), max_length=150)
    email = models.EmailField(_("email"))
    phone = PhoneNumberField(_("phone"))
    prefers_whatsapp = models.BooleanField(_("prefers WhatsApp"), default=True)
    country = CountryField(verbose_name=_("country"))
    patient_age = models.PositiveSmallIntegerField(
        _("patient's age"), null=True, blank=True
    )

    # What they need.
    treatment = models.ForeignKey(
        Treatment,
        verbose_name=_("treatment"),
        on_delete=models.SET_NULL,
        related_name="enquiries",
        null=True,
        blank=True,
    )
    hospital = models.ForeignKey(
        Hospital,
        verbose_name=_("hospital"),
        on_delete=models.SET_NULL,
        related_name="enquiries",
        null=True,
        blank=True,
    )
    doctor = models.ForeignKey(
        Doctor,
        verbose_name=_("doctor"),
        on_delete=models.SET_NULL,
        related_name="enquiries",
        null=True,
        blank=True,
    )
    message = models.TextField(_("medical details and questions"), max_length=5000)

    # Case management.
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=EnquiryStatus.choices,
        default=EnquiryStatus.NEW,
        db_index=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("case manager"),
        on_delete=models.SET_NULL,
        related_name="assigned_enquiries",
        null=True,
        blank=True,
    )
    internal_notes = models.TextField(_("internal notes"), blank=True)

    # Where the lead came from (for marketing attribution).
    landing_page = models.CharField(_("landing page"), max_length=500, blank=True)
    referrer = models.CharField(_("referrer"), max_length=500, blank=True)
    utm_source = models.CharField(_("UTM source"), max_length=200, blank=True)
    utm_medium = models.CharField(_("UTM medium"), max_length=200, blank=True)
    utm_campaign = models.CharField(_("UTM campaign"), max_length=200, blank=True)
    utm_term = models.CharField(_("UTM term"), max_length=200, blank=True)
    utm_content = models.CharField(_("UTM content"), max_length=200, blank=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = _("enquiry")
        verbose_name_plural = _("enquiries")
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference


class EnquiryDocument(models.Model):
    """A medical report uploaded with an enquiry. Stored privately."""

    enquiry = models.ForeignKey(
        Enquiry,
        verbose_name=_("enquiry"),
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(
        _("file"), upload_to=enquiry_document_path, storage=private_storage
    )
    original_name = models.CharField(_("original file name"), max_length=255)
    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)

    class Meta:
        verbose_name = _("medical document")
        verbose_name_plural = _("medical documents")
        ordering = ["uploaded_at"]

    def __str__(self):
        return self.original_name


class ConsentPurpose(models.TextChoices):
    PROCESS_ENQUIRY = "process_enquiry", _("Process my enquiry")
    MARKETING = "marketing", _("Marketing updates")


class ConsentRecord(models.Model):
    """Proof of exactly what a patient agreed to, and when (DPDP Act).

    The full consent text is copied in, so the record stays accurate even
    after the wording on the website changes. Records are never edited:
    withdrawing consent sets `withdrawn_at`.
    """

    enquiry = models.ForeignKey(
        Enquiry,
        verbose_name=_("enquiry"),
        on_delete=models.CASCADE,
        related_name="consents",
    )
    purpose = models.CharField(
        _("purpose"), max_length=30, choices=ConsentPurpose.choices
    )
    consent_text_version = models.CharField(_("consent text version"), max_length=30)
    consent_text = models.TextField(_("consent text shown"))
    granted_at = models.DateTimeField(_("granted at"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    user_agent = models.CharField(_("browser"), max_length=300, blank=True)
    withdrawn_at = models.DateTimeField(_("withdrawn at"), null=True, blank=True)

    class Meta:
        verbose_name = _("consent record")
        verbose_name_plural = _("consent records")
        ordering = ["granted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["enquiry", "purpose"],
                name="leads_consent_one_per_purpose",
            ),
        ]
        indexes = [
            # Used by the per-IP submission limit.
            models.Index(fields=["ip_address", "granted_at"]),
        ]

    def __str__(self):
        return f"{self.enquiry}: {self.get_purpose_display()}"
