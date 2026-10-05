from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Treatment
from apps.core.models import PublishableModel, TimeStampedModel
from apps.providers.models import Hospital


class TreatmentPackage(TimeStampedModel, PublishableModel):
    """A hospital's indicative price for a treatment, in rupees.

    These are estimates from hospital quotes, never guaranteed prices: the
    final cost depends on the patient's condition and the hospital's
    assessment. The site must always present them that way.
    """

    treatment = models.ForeignKey(
        Treatment,
        verbose_name=_("treatment"),
        on_delete=models.PROTECT,
        related_name="packages",
    )
    hospital = models.ForeignKey(
        Hospital,
        verbose_name=_("hospital"),
        on_delete=models.PROTECT,
        related_name="packages",
    )
    price_min_inr = models.PositiveIntegerField(
        _("starting price (₹)"), validators=[MinValueValidator(1)]
    )
    price_max_inr = models.PositiveIntegerField(
        _("upper price (₹)"),
        null=True,
        blank=True,
        help_text=_("Leave blank if the hospital quoted a single price."),
    )
    inclusions = models.TextField(
        _("included"),
        blank=True,
        help_text=_("One item per line. Example: 5 nights in a private room."),
    )
    exclusions = models.TextField(
        _("not included"),
        blank=True,
        help_text=_("One item per line. Example: Implant upgrades."),
    )
    price_updated_on = models.DateField(
        _("price confirmed on"),
        default=timezone.localdate,
        help_text=_("When the hospital last confirmed this price."),
    )

    class Meta:
        verbose_name = _("treatment package")
        verbose_name_plural = _("treatment packages")
        ordering = ["price_min_inr"]
        constraints = [
            models.UniqueConstraint(
                fields=["treatment", "hospital"],
                name="pricing_package_unique_treatment_hospital",
                violation_error_message=_(
                    "This hospital already has a package for this treatment."
                ),
            ),
            models.CheckConstraint(
                condition=Q(price_max_inr__isnull=True)
                | Q(price_max_inr__gte=F("price_min_inr")),
                name="pricing_package_max_at_least_min",
                violation_error_message=_(
                    "The upper price cannot be lower than the starting price."
                ),
            ),
        ]

    def __str__(self):
        return f"{self.treatment.name} at {self.hospital.name}"

    def clean(self):
        super().clean()
        # Keep each hospital's speciality list complete: it drives pages such
        # as "cardiology hospitals in India".
        if self.treatment_id and self.hospital_id:
            offers_speciality = self.hospital.specialities.filter(
                pk=self.treatment.speciality_id
            ).exists()
            if not offers_speciality:
                raise ValidationError(
                    {
                        "hospital": _(
                            "Add %(speciality)s to this hospital's specialities "
                            "before giving it a %(treatment)s package."
                        )
                        % {
                            "speciality": self.treatment.speciality,
                            "treatment": self.treatment,
                        }
                    }
                )

    @property
    def price_upper_inr(self) -> int:
        return self.price_max_inr or self.price_min_inr

    @property
    def inclusion_list(self) -> list[str]:
        return _non_empty_lines(self.inclusions)

    @property
    def exclusion_list(self) -> list[str]:
        return _non_empty_lines(self.exclusions)


def _non_empty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


class DisplayCurrency(models.TextChoices):
    """Currencies prices are also shown in, next to rupees."""

    USD = "USD", _("US dollar")
    EUR = "EUR", _("Euro")
    GBP = "GBP", _("British pound")


class ExchangeRate(models.Model):
    """Daily reference rate, updated by the `update_exchange_rates` command."""

    currency = models.CharField(
        _("currency"), max_length=3, unique=True, choices=DisplayCurrency.choices
    )
    inr_per_unit = models.DecimalField(
        _("rupees per unit"), max_digits=12, decimal_places=4
    )
    rate_date = models.DateField(_("rate date"))
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("exchange rate")
        verbose_name_plural = _("exchange rates")
        ordering = ["currency"]

    def __str__(self):
        return f"1 {self.currency} = ₹{self.inr_per_unit}"
