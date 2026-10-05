from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.core.models import SLUG_HELP_TEXT, PublishableModel, TimeStampedModel
from apps.core.search import SEARCH_CONFIG

ALSO_KNOWN_AS_HELP_TEXT = _(
    "Other names and abbreviations patients search for, comma separated. "
    "Example: TKR, knee arthroplasty."
)
SUMMARY_HELP_TEXT = _(
    "One or two plain sentences. Shown on listing cards and used as the "
    "default search-engine description."
)


def search_vector_expression():
    """Names count most (weight A); the summary counts less (weight B)."""
    return (
        SearchVector("name", weight="A", config=SEARCH_CONFIG)
        + SearchVector("also_known_as", weight="A", config=SEARCH_CONFIG)
        + SearchVector("summary", weight="B", config=SEARCH_CONFIG)
    )


class Speciality(TimeStampedModel, PublishableModel):
    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(
        _("slug"), max_length=100, unique=True, help_text=SLUG_HELP_TEXT
    )
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=SUMMARY_HELP_TEXT
    )
    description = models.TextField(_("description"), blank=True)
    display_order = models.PositiveSmallIntegerField(
        _("display order"), default=0, help_text=_("Lower numbers appear first.")
    )

    class Meta:
        verbose_name = _("speciality")
        verbose_name_plural = _("specialities")
        ordering = ["display_order", "name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="catalog_speciality_unique_name",
                violation_error_message=_(
                    "A speciality with this name already exists."
                ),
            ),
        ]

    def __str__(self):
        return self.name


class Treatment(TimeStampedModel, PublishableModel):
    speciality = models.ForeignKey(
        Speciality,
        verbose_name=_("speciality"),
        on_delete=models.PROTECT,
        related_name="treatments",
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
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=SUMMARY_HELP_TEXT
    )
    description = models.TextField(_("description"), blank=True)
    hospital_stay_days = models.PositiveSmallIntegerField(
        _("hospital stay (days)"),
        null=True,
        blank=True,
        help_text=_("Typical number of days admitted in hospital."),
    )
    stay_in_india_days = models.PositiveSmallIntegerField(
        _("total stay in India (days)"),
        null=True,
        blank=True,
        help_text=_("Typical total stay, including recovery before flying home."),
    )
    search_vector = models.GeneratedField(
        expression=search_vector_expression(),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        verbose_name = _("treatment")
        verbose_name_plural = _("treatments")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["search_vector"], name="catalog_treatment_search_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="catalog_treatment_unique_name",
                violation_error_message=_("A treatment with this name already exists."),
            ),
            models.CheckConstraint(
                condition=Q(hospital_stay_days__isnull=True)
                | Q(stay_in_india_days__isnull=True)
                | Q(stay_in_india_days__gte=F("hospital_stay_days")),
                name="catalog_treatment_stay_covers_hospital_stay",
                violation_error_message=_(
                    "Total stay in India cannot be shorter than the hospital stay."
                ),
            ),
        ]

    def __str__(self):
        return self.name


class Condition(TimeStampedModel, PublishableModel):
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
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=SUMMARY_HELP_TEXT
    )
    description = models.TextField(_("description"), blank=True)
    treatments = models.ManyToManyField(
        Treatment,
        verbose_name=_("treatments"),
        related_name="conditions",
        blank=True,
        help_text=_("Treatments that address this condition."),
    )
    search_vector = models.GeneratedField(
        expression=search_vector_expression(),
        output_field=SearchVectorField(),
        db_persist=True,
    )

    class Meta:
        verbose_name = _("condition")
        verbose_name_plural = _("conditions")
        ordering = ["name"]
        indexes = [
            GinIndex(fields=["search_vector"], name="catalog_condition_search_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="catalog_condition_unique_name",
                violation_error_message=_("A condition with this name already exists."),
            ),
        ]

    def __str__(self):
        return self.name
