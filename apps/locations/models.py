from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from apps.core.models import SLUG_HELP_TEXT, PublishableModel, TimeStampedModel
from apps.core.rich_text import RichTextField

# India's 28 states and 8 union territories. Stored exactly as displayed.
INDIAN_STATES_AND_UTS = (
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
)
STATE_CHOICES = [(name, name) for name in INDIAN_STATES_AND_UTS]


class City(TimeStampedModel, PublishableModel):
    """An Indian city where partner hospitals are located (treatment destination)."""

    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(
        _("slug"),
        max_length=100,
        unique=True,
        help_text=SLUG_HELP_TEXT,
    )
    state = models.CharField(
        _("state / union territory"), max_length=100, choices=STATE_CHOICES
    )

    class Meta:
        verbose_name = _("city")
        verbose_name_plural = _("cities")
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                Lower("state"),
                name="locations_city_unique_name_state",
                violation_error_message=_("This city already exists in this state."),
            ),
        ]

    def __str__(self):
        return self.name


class SourceCountry(TimeStampedModel, PublishableModel):
    """A country patients travel FROM.

    Powers pages such as /medical-travel-from-bangladesh-to-india/.
    """

    country = CountryField(verbose_name=_("country"), unique=True)
    slug = models.SlugField(
        _("slug"),
        max_length=100,
        unique=True,
        blank=True,
        help_text=_("Leave blank to generate it from the country name."),
    )
    intro = RichTextField(_("introduction"), blank=True)
    visa_info = RichTextField(_("visa information"), blank=True)

    class Meta:
        verbose_name = _("source country")
        verbose_name_plural = _("source countries")
        ordering = ["country"]

    def __str__(self):
        return self.country.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.country.name)
        super().save(*args, **kwargs)
