from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Max, Min, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.catalog.models import Treatment
from apps.catalog.selectors import published_treatments
from apps.providers.models import Hospital
from apps.providers.selectors import current_accreditations

from .models import ExchangeRate, TreatmentPackage

# ECB rates aren't published on weekends and holidays. Older than this, a
# rate is treated as broken and foreign-currency prices are hidden.
MAX_RATE_AGE_DAYS = 7


@dataclass(frozen=True)
class CostSummary:
    min_inr: int
    max_inr: int
    hospital_count: int


def published_packages() -> QuerySet[TreatmentPackage]:
    """Packages visitors may see: the package and everything it belongs to
    (treatment, speciality, hospital, city) must be published."""
    return TreatmentPackage.objects.published().filter(
        treatment__is_published=True,
        treatment__speciality__is_published=True,
        hospital__is_published=True,
        hospital__city__is_published=True,
    )


def packages_for_treatment(treatment: Treatment) -> QuerySet[TreatmentPackage]:
    """The cost table on a treatment page, cheapest first."""
    return (
        published_packages()
        .filter(treatment=treatment)
        .select_related("hospital__city")
        .prefetch_related(current_accreditations("hospital__"))
        .order_by("price_min_inr", "hospital__name")
    )


def cost_summary(treatment: Treatment) -> CostSummary | None:
    """Price range across hospitals, e.g. "₹2,50,000 to ₹4,50,000 at 6 hospitals"."""
    totals = (
        published_packages()
        .filter(treatment=treatment)
        .aggregate(
            min_inr=Min("price_min_inr"),
            max_inr=Max(Coalesce("price_max_inr", "price_min_inr")),
            hospital_count=Count("hospital", distinct=True),
        )
    )
    if not totals["hospital_count"]:
        return None
    return CostSummary(**totals)


def with_starting_price(treatments: QuerySet[Treatment]) -> QuerySet[Treatment]:
    """Add `starting_price_inr` to each treatment ("from ₹X"), or None."""
    cheapest = (
        published_packages()
        .filter(treatment=OuterRef("pk"))
        .order_by("price_min_inr")
        .values("price_min_inr")[:1]
    )
    return treatments.annotate(starting_price_inr=Subquery(cheapest))


def treatments_with_prices() -> QuerySet[Treatment]:
    """Published treatments with at least one public price, most hospitals first.

    Each treatment gets `price_from_inr`, `price_to_inr`, `hospital_count` and
    `prices_updated_on` (the most recent confirmation), for cards such as
    "from ₹2,50,000, up to ₹4,50,000, at 6 hospitals, updated 3 Oct".
    """
    # One row per treatment: order_by() drops the model's default ordering,
    # which would otherwise split the GROUP BY.
    packages = (
        published_packages()
        .filter(treatment=OuterRef("pk"))
        .order_by()
        .values("treatment")
    )

    def per_treatment(aggregate):
        return Subquery(packages.annotate(value=aggregate).values("value"))

    return (
        published_treatments()
        .annotate(
            price_from_inr=per_treatment(Min("price_min_inr")),
            price_to_inr=per_treatment(Max(Coalesce("price_max_inr", "price_min_inr"))),
            hospital_count=per_treatment(Count("hospital", distinct=True)),
            prices_updated_on=per_treatment(Max("price_updated_on")),
        )
        .filter(hospital_count__gt=0)
        .order_by("-hospital_count", "name")
    )


def current_inr_per_unit(currency: str) -> Decimal | None:
    """Today's usable rate for `currency`, or None if missing or stale."""
    oldest_allowed = timezone.localdate() - timedelta(days=MAX_RATE_AGE_DAYS)
    return (
        ExchangeRate.objects.filter(currency=currency, rate_date__gte=oldest_allowed)
        .values_list("inr_per_unit", flat=True)
        .first()
    )


def packages_at_hospital(hospital: Hospital) -> QuerySet[TreatmentPackage]:
    """The price list on a hospital page, by treatment name."""
    return (
        published_packages()
        .filter(hospital=hospital)
        .select_related("treatment")
        .order_by("treatment__name")
    )
