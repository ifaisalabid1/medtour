from model_bakery.recipe import Recipe, foreign_key, seq

from apps.catalog.models import Condition, Speciality, Treatment

speciality = Recipe(
    Speciality,
    name=seq("Speciality "),
    slug=seq("speciality-"),
    is_published=True,
)

treatment = Recipe(
    Treatment,
    speciality=foreign_key(speciality),
    name=seq("Treatment "),
    slug=seq("treatment-"),
    is_published=True,
)

condition = Recipe(
    Condition,
    name=seq("Condition "),
    slug=seq("condition-"),
    is_published=True,
)
