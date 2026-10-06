from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Speciality
from apps.core.models import (
    ALSO_KNOWN_AS_HELP_TEXT,
    SLUG_HELP_TEXT,
    SUMMARY_HELP_TEXT,
    PublishableModel,
    TimeStampedModel,
)
from apps.core.rich_text import RichTextField
from apps.core.search import weighted_search_vector
from apps.core.uploads import unique_upload_path
from apps.core.validators import (
    current_year,
    validate_image_extension,
    validate_image_size,
    validate_indian_pincode,
)
from apps.locations.models import City


def hospital_image_path(instance, filename):
    return unique_upload_path("hospitals", filename)


def doctor_photo_path(instance, filename):
    return unique_upload_path("doctors", filename)


class Accreditation(TimeStampedModel):
    """A quality certification body, e.g. NABH or JCI."""

    abbreviation = models.CharField(_("abbreviation"), max_length=20, unique=True)
    name = models.CharField(_("full name"), max_length=200, unique=True)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        verbose_name = _("accreditation")
        verbose_name_plural = _("accreditations")
        ordering = ["abbreviation"]

    def __str__(self):
        return self.abbreviation


class Hospital(TimeStampedModel, PublishableModel):
    city = models.ForeignKey(
        City,
        verbose_name=_("city"),
        on_delete=models.PROTECT,
        related_name="hospitals",
    )
    name = models.CharField(_("name"), max_length=200)
    slug = models.SlugField(
        _("slug"), max_length=200, unique=True, help_text=SLUG_HELP_TEXT
    )
    also_known_as = models.CharField(
        _("also known as"),
        max_length=255,
        blank=True,
        help_text=ALSO_KNOWN_AS_HELP_TEXT,
    )
    address = models.CharField(_("street address"), max_length=255, blank=True)
    postal_code = models.CharField(
        _("PIN code"),
        max_length=6,
        blank=True,
        validators=[validate_indian_pincode],
    )
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=SUMMARY_HELP_TEXT
    )
    description = RichTextField(_("description"), blank=True)
    established_year = models.PositiveSmallIntegerField(
        _("year established"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1800), MaxValueValidator(current_year)],
    )
    bed_count = models.PositiveIntegerField(_("number of beds"), null=True, blank=True)
    image = models.ImageField(
        _("main image"),
        upload_to=hospital_image_path,
        blank=True,
        validators=[validate_image_extension, validate_image_size],
        help_text=_("JPG, PNG or WebP, up to 5 MB. Landscape works best."),
    )
    specialities = models.ManyToManyField(
        Speciality,
        verbose_name=_("specialities"),
        related_name="hospitals",
        blank=True,
    )
    accreditations = models.ManyToManyField(
        Accreditation,
        verbose_name=_("accreditations"),
        through="HospitalAccreditation",
        related_name="hospitals",
        blank=True,
    )
    search_vector = models.GeneratedField(
        expression=weighted_search_vector(
            primary=("name", "also_known_as"), secondary=("summary",)
        ),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        verbose_name = _("hospital")
        verbose_name_plural = _("hospitals")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["search_vector"], name="providers_hospital_search_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                "city",
                name="providers_hospital_unique_name_per_city",
                violation_error_message=_(
                    "A hospital with this name already exists in this city."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.name}, {self.city}"

    def get_absolute_url(self):
        return reverse("website:hospital_detail", kwargs={"slug": self.slug})


class HospitalAccreditation(models.Model):
    """A hospital's accreditation, with its expiry date.

    Accreditations lapse. Showing an expired NABH/JCI badge is misleading, so
    the public site only shows records that are still valid.
    """

    hospital = models.ForeignKey(
        Hospital,
        verbose_name=_("hospital"),
        on_delete=models.CASCADE,
        related_name="accreditation_records",
    )
    accreditation = models.ForeignKey(
        Accreditation,
        verbose_name=_("accreditation"),
        on_delete=models.PROTECT,
        related_name="hospital_records",
    )
    certificate_number = models.CharField(
        _("certificate number"), max_length=100, blank=True
    )
    valid_until = models.DateField(
        _("valid until"),
        null=True,
        blank=True,
        help_text=_("Leave blank only if the accreditation does not expire."),
    )

    class Meta:
        verbose_name = _("hospital accreditation")
        verbose_name_plural = _("hospital accreditations")
        constraints = [
            models.UniqueConstraint(
                fields=["hospital", "accreditation"],
                name="providers_hospitalaccreditation_unique",
                violation_error_message=_(
                    "This hospital already has this accreditation."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.hospital.name}: {self.accreditation}"


class Doctor(TimeStampedModel, PublishableModel):
    name = models.CharField(
        _("name"),
        max_length=150,
        help_text=_('Without the "Dr." prefix. The site adds it.'),
    )
    slug = models.SlugField(
        _("slug"), max_length=150, unique=True, help_text=SLUG_HELP_TEXT
    )
    designation = models.CharField(
        _("designation"),
        max_length=200,
        blank=True,
        help_text=_("Example: Chairman, Institute of Orthopaedics."),
    )
    qualifications = models.CharField(
        _("qualifications"),
        max_length=255,
        blank=True,
        help_text=_("Example: MBBS, MS (Orthopaedics), FRCS."),
    )
    practising_since = models.PositiveSmallIntegerField(
        _("practising since (year)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1950), MaxValueValidator(current_year)],
        help_text=_(
            "Year the doctor started practising. Experience is calculated "
            "from this, so it never goes out of date."
        ),
    )
    medical_registration_number = models.CharField(
        _("medical registration number"),
        max_length=50,
        blank=True,
        help_text=_("NMC or state medical council registration. Internal only."),
    )
    registration_verified_on = models.DateField(
        _("registration verified on"),
        null=True,
        blank=True,
        help_text=_(
            "Date the team checked the number on the NMC or state medical council "
            'register. The site shows "Registration verified" only when this is set.'
        ),
    )
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=SUMMARY_HELP_TEXT
    )
    description = RichTextField(_("description"), blank=True)
    photo = models.ImageField(
        _("photo"),
        upload_to=doctor_photo_path,
        blank=True,
        validators=[validate_image_extension, validate_image_size],
        help_text=_("JPG, PNG or WebP, up to 5 MB. Square works best."),
    )
    specialities = models.ManyToManyField(
        Speciality,
        verbose_name=_("specialities"),
        related_name="doctors",
        blank=True,
    )
    hospitals = models.ManyToManyField(
        Hospital,
        verbose_name=_("hospitals"),
        related_name="doctors",
        blank=True,
    )
    search_vector = models.GeneratedField(
        expression=weighted_search_vector(
            primary=("name",), secondary=("designation", "summary")
        ),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        verbose_name = _("doctor")
        verbose_name_plural = _("doctors")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["search_vector"], name="providers_doctor_search_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(registration_verified_on__isnull=True)
                | ~Q(medical_registration_number=""),
                name="providers_doctor_verified_registration_has_number",
                violation_error_message=_(
                    "Enter the registration number before marking it verified."
                ),
            ),
        ]

    def __str__(self):
        return f"Dr. {self.name}"

    def get_absolute_url(self):
        return reverse("website:doctor_detail", kwargs={"slug": self.slug})

    @property
    def years_of_experience(self) -> int | None:
        if self.practising_since is None:
            return None
        return timezone.localdate().year - self.practising_since
