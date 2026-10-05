from django.db.models import QuerySet

from .models import City, SourceCountry


def published_cities() -> QuerySet[City]:
    return City.objects.published()


def published_source_countries() -> QuerySet[SourceCountry]:
    return SourceCountry.objects.published()
