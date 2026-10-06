from django.contrib.postgres.search import SearchRank
from django.db.models import Count, F, Prefetch, Q, QuerySet
from django.utils import timezone

from apps.catalog.models import Speciality
from apps.catalog.selectors import published_specialities
from apps.core.search import build_prefix_search_query
from apps.locations.models import City
from apps.locations.selectors import published_cities

from .models import Doctor, Hospital, HospitalAccreditation


def current_accreditations(prefix: str = "") -> Prefetch:
    """Accreditations that haven't expired, as `hospital.current_accreditations`.

    `prefix` reaches hospitals through a relation, e.g. "hospital__" to load
    them for the hospitals of a list of packages.
    """
    today = timezone.localdate()
    return Prefetch(
        f"{prefix}accreditation_records",
        queryset=HospitalAccreditation.objects.filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=today)
        ).select_related("accreditation"),
        to_attr="current_accreditations",
    )


def published_hospitals() -> QuerySet[Hospital]:
    """Hospitals visitors may see: published and in a published city."""
    return (
        Hospital.objects.published()
        .filter(city__is_published=True)
        .select_related("city")
        .prefetch_related(current_accreditations())
    )


def published_doctors() -> QuerySet[Doctor]:
    """Published doctors, with only their public hospitals and specialities.

    Use `doctor.public_hospitals` and `doctor.public_specialities` in templates,
    never `doctor.hospitals.all()`, which would include unpublished ones.
    """
    return Doctor.objects.published().prefetch_related(
        Prefetch(
            "hospitals", queryset=published_hospitals(), to_attr="public_hospitals"
        ),
        Prefetch(
            "specialities",
            queryset=published_specialities(),
            to_attr="public_specialities",
        ),
    )


def search_hospitals(text: str) -> QuerySet[Hospital]:
    query = build_prefix_search_query(text)
    if query is None:
        return Hospital.objects.none()
    return (
        published_hospitals()
        .filter(search_vector=query)
        .annotate(rank=SearchRank(F("search_vector"), query))
        .order_by("-rank", "name")
    )


def search_doctors(text: str) -> QuerySet[Doctor]:
    query = build_prefix_search_query(text)
    if query is None:
        return Doctor.objects.none()
    return (
        published_doctors()
        .filter(search_vector=query)
        .annotate(rank=SearchRank(F("search_vector"), query))
        .order_by("-rank", "name")
    )


def hospitals_for_speciality(speciality: Speciality) -> QuerySet[Hospital]:
    return published_hospitals().filter(specialities=speciality)


def doctors_for_speciality(speciality: Speciality) -> QuerySet[Doctor]:
    return published_doctors().filter(specialities=speciality)


def doctors_at_hospital(hospital: Hospital) -> QuerySet[Doctor]:
    return published_doctors().filter(hospitals=hospital)


def cities_with_hospitals() -> QuerySet[City]:
    """Published cities with at least one public hospital, most hospitals first."""
    return (
        published_cities()
        .annotate(
            hospital_count=Count("hospitals", filter=Q(hospitals__is_published=True))
        )
        .filter(hospital_count__gt=0)
        .order_by("-hospital_count", "name")
    )


def hospitals_in_city(city: City | None) -> QuerySet[Hospital]:
    """Public hospitals, largest first; in every city when `city` is None."""
    hospitals = published_hospitals()
    if city is not None:
        hospitals = hospitals.filter(city=city)
    return hospitals.order_by(F("bed_count").desc(nulls_last=True), "name")


def doctors_by_experience() -> QuerySet[Doctor]:
    """Public doctors, longest in practice first."""
    return published_doctors().order_by(
        F("practising_since").asc(nulls_last=True), "name"
    )
