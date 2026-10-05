from itertools import cycle

from model_bakery.recipe import Recipe, seq

from apps.locations.models import City, SourceCountry

city = Recipe(
    City,
    name=seq("City "),
    slug=seq("city-"),
    state="Maharashtra",
    is_published=True,
)

source_country = Recipe(
    SourceCountry,
    country=cycle(["BD", "NP", "NG", "KE", "IQ", "OM"]),
    is_published=True,
)
