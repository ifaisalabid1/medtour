from model_bakery.recipe import Recipe, foreign_key, seq

from apps.locations.tests.baker_recipes import city
from apps.providers.models import Accreditation, Doctor, Hospital

accreditation = Recipe(
    Accreditation,
    abbreviation=seq("ACC"),
    name=seq("Accreditation body "),
)

hospital = Recipe(
    Hospital,
    city=foreign_key(city),
    name=seq("Hospital "),
    slug=seq("hospital-"),
    is_published=True,
)

doctor = Recipe(
    Doctor,
    name=seq("Doctor "),
    slug=seq("doctor-"),
    is_published=True,
)
