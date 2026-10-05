from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from apps.catalog.models import Condition, Treatment
from apps.core.models import (
    SLUG_HELP_TEXT,
    SUMMARY_HELP_TEXT,
    PublishableModel,
    TimeStampedModel,
)
from apps.core.rich_text import BasicRichTextField, RichTextField
from apps.core.uploads import unique_upload_path
from apps.core.validators import validate_image_extension, validate_image_size
from apps.providers.models import Doctor, Hospital


def author_photo_path(instance, filename):
    return unique_upload_path("authors", filename)


def article_image_path(instance, filename):
    return unique_upload_path("articles", filename)


class Author(TimeStampedModel):
    """A named writer or medical reviewer shown in article bylines.

    Real, credentialed people behind medical content are what Google's
    guidelines for health pages look for.
    """

    name = models.CharField(_("name"), max_length=150)
    slug = models.SlugField(
        _("slug"), max_length=150, unique=True, help_text=SLUG_HELP_TEXT
    )
    credentials = models.CharField(
        _("credentials"),
        max_length=255,
        blank=True,
        help_text=_("Example: MBBS, MD (Internal Medicine)."),
    )
    bio = models.TextField(_("short bio"), blank=True)
    photo = models.ImageField(
        _("photo"),
        upload_to=author_photo_path,
        blank=True,
        validators=[validate_image_extension, validate_image_size],
    )
    is_medical_professional = models.BooleanField(
        _("registered medical professional"),
        default=False,
        help_text=_("Only medical professionals can be chosen as medical reviewers."),
    )
    medical_registration_number = models.CharField(
        _("medical registration number"),
        max_length=50,
        blank=True,
        help_text=_("NMC or state medical council registration. Internal only."),
    )

    class Meta:
        verbose_name = _("author")
        verbose_name_plural = _("authors")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Article(TimeStampedModel, PublishableModel):
    """A knowledge-centre article.

    Medical content must be reviewed by a medical professional before it is
    published. The database enforces this.
    """

    title = models.CharField(_("title"), max_length=200)
    slug = models.SlugField(
        _("slug"), max_length=200, unique=True, help_text=SLUG_HELP_TEXT
    )
    summary = models.CharField(
        _("summary"), max_length=300, help_text=SUMMARY_HELP_TEXT
    )
    body = RichTextField(_("body"))
    cover_image = models.ImageField(
        _("cover image"),
        upload_to=article_image_path,
        blank=True,
        validators=[validate_image_extension, validate_image_size],
    )
    author = models.ForeignKey(
        Author,
        verbose_name=_("author"),
        on_delete=models.PROTECT,
        related_name="articles",
    )
    medical_reviewer = models.ForeignKey(
        Author,
        verbose_name=_("medical reviewer"),
        on_delete=models.PROTECT,
        related_name="reviewed_articles",
        null=True,
        blank=True,
        limit_choices_to={"is_medical_professional": True},
    )
    reviewed_on = models.DateField(
        _("medically reviewed on"),
        null=True,
        blank=True,
        help_text=_("Update this every time the content is re-reviewed."),
    )
    published_at = models.DateTimeField(
        _("first published at"),
        null=True,
        blank=True,
        editable=False,
    )
    treatments = models.ManyToManyField(
        Treatment,
        verbose_name=_("related treatments"),
        related_name="articles",
        blank=True,
    )
    conditions = models.ManyToManyField(
        Condition,
        verbose_name=_("related conditions"),
        related_name="articles",
        blank=True,
    )

    class Meta:
        verbose_name = _("article")
        verbose_name_plural = _("articles")
        ordering = ["-published_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(is_published=False)
                | Q(medical_reviewer__isnull=False, reviewed_on__isnull=False),
                name="content_article_reviewed_before_publishing",
                violation_error_message=_(
                    "Add a medical reviewer and review date before publishing."
                ),
            ),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        # limit_choices_to only filters the admin's choices; enforce it here too.
        if self.medical_reviewer and not self.medical_reviewer.is_medical_professional:
            raise ValidationError(
                {"medical_reviewer": _("The reviewer must be a medical professional.")}
            )

    def save(self, *args, **kwargs):
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("website:article_detail", kwargs={"slug": self.slug})


class FAQ(TimeStampedModel, PublishableModel):
    """A question and answer shown on exactly one treatment or condition page."""

    question = models.CharField(_("question"), max_length=255)
    answer = BasicRichTextField(_("answer"))
    treatment = models.ForeignKey(
        Treatment,
        verbose_name=_("treatment"),
        on_delete=models.CASCADE,
        related_name="faqs",
        null=True,
        blank=True,
    )
    condition = models.ForeignKey(
        Condition,
        verbose_name=_("condition"),
        on_delete=models.CASCADE,
        related_name="faqs",
        null=True,
        blank=True,
    )
    display_order = models.PositiveSmallIntegerField(
        _("display order"), default=0, help_text=_("Lower numbers appear first.")
    )

    class Meta:
        verbose_name = _("FAQ")
        verbose_name_plural = _("FAQs")
        ordering = ["display_order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=Q(treatment__isnull=False, condition__isnull=True)
                | Q(treatment__isnull=True, condition__isnull=False),
                name="content_faq_exactly_one_page",
                violation_error_message=_(
                    "Choose either a treatment or a condition (not both)."
                ),
            ),
        ]

    def __str__(self):
        return self.question


class Testimonial(TimeStampedModel, PublishableModel):
    """A patient's story. Never published without the patient's recorded consent.

    Under the DPDP Act a patient's story is personal (health) data: publishing
    it needs their explicit consent, so the database refuses to publish one
    without a consent date.
    """

    patient_display_name = models.CharField(
        _("patient name as shown"),
        max_length=100,
        help_text=_('Use what the patient agreed to, e.g. "Rahim U." or initials.'),
    )
    country = CountryField(verbose_name=_("patient's country"))
    quote = models.TextField(_("testimonial"), max_length=1500)
    video_url = models.URLField(
        _("video link"),
        blank=True,
        help_text=_("YouTube link, if the patient recorded a video."),
    )
    treatment = models.ForeignKey(
        Treatment,
        verbose_name=_("treatment"),
        on_delete=models.SET_NULL,
        related_name="testimonials",
        null=True,
        blank=True,
    )
    hospital = models.ForeignKey(
        Hospital,
        verbose_name=_("hospital"),
        on_delete=models.SET_NULL,
        related_name="testimonials",
        null=True,
        blank=True,
    )
    doctor = models.ForeignKey(
        Doctor,
        verbose_name=_("doctor"),
        on_delete=models.SET_NULL,
        related_name="testimonials",
        null=True,
        blank=True,
    )
    treated_on = models.DateField(_("treated on"), null=True, blank=True)
    consent_obtained_on = models.DateField(
        _("consent obtained on"),
        null=True,
        blank=True,
        help_text=_("Date the patient agreed in writing to publish this."),
    )
    consent_reference = models.CharField(
        _("where the consent is filed"),
        max_length=255,
        blank=True,
        help_text=_(
            "Internal only. Example: signed form in the case file of enquiry 1042."
        ),
    )

    class Meta:
        verbose_name = _("testimonial")
        verbose_name_plural = _("testimonials")
        ordering = ["-treated_on", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(is_published=False) | Q(consent_obtained_on__isnull=False),
                name="content_testimonial_consent_before_publishing",
                violation_error_message=_(
                    "Record the patient's consent before publishing."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.patient_display_name} ({self.country.name})"
