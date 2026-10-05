from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Max, Min, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.catalog.models import Treatment

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


def current_inr_per_unit(currency: str) -> Decimal | None:
    """Today's usable rate for `currency`, or None if missing or stale."""
    oldest_allowed = timezone.localdate() - timedelta(days=MAX_RATE_AGE_DAYS)
    return (
        ExchangeRate.objects.filter(currency=currency, rate_date__gte=oldest_allowed)
        .values_list("inr_per_unit", flat=True)
        .first()
    )
