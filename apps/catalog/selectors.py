from django.contrib.postgres.search import SearchRank
from django.db.models import Exists, F, OuterRef, Q, QuerySet

from apps.core.search import build_prefix_search_query

from .models import Condition, Speciality, Treatment


def published_specialities() -> QuerySet[Speciality]:
    return Speciality.objects.published()


def published_treatments() -> QuerySet[Treatment]:
    """Treatments visitors may see: published and in a published speciality."""
    return (
        Treatment.objects.published()
        .filter(speciality__is_published=True)
        .select_related("speciality")
    )


def published_conditions() -> QuerySet[Condition]:
    return Condition.objects.published()


def search_treatments(text: str) -> QuerySet[Treatment]:
    """Published treatments matching the text, best matches first.

    Matches the treatment's name, alternative names and summary, or a linked
    published condition (so "arthritis" finds knee replacement).
    """
    query = build_prefix_search_query(text)
    if query is None:
        return Treatment.objects.none()

    matches_linked_condition = Exists(
        Condition.treatments.through.objects.filter(
            treatment=OuterRef("pk"),
            condition__is_published=True,
            condition__search_vector=query,
        )
    )
    return (
        published_treatments()
        .filter(Q(search_vector=query) | matches_linked_condition)
        # F() is required: a plain string is re-parsed as text, which loses
        # the A/B weights that rank name matches above summary matches.
        .annotate(rank=SearchRank(F("search_vector"), query))
        .order_by("-rank", "name")
    )


def treatments_in_speciality(speciality: Speciality) -> QuerySet[Treatment]:
    return published_treatments().filter(speciality=speciality)


def treatments_for_condition(condition: Condition) -> QuerySet[Treatment]:
    return published_treatments().filter(conditions=condition)
