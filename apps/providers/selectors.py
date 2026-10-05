from django.contrib.postgres.search import SearchRank
from django.db.models import F, Prefetch, Q, QuerySet
from django.utils import timezone

from apps.catalog.models import Speciality
from apps.catalog.selectors import published_specialities
from apps.core.search import build_prefix_search_query

from .models import Doctor, Hospital, HospitalAccreditation


def _current_accreditations() -> Prefetch:
    """Accreditations that haven't expired, as `hospital.current_accreditations`."""
    today = timezone.localdate()
    return Prefetch(
        "accreditation_records",
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
        .prefetch_related(_current_accreditations())
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
