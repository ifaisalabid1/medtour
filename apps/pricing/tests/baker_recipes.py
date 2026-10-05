from model_bakery.recipe import Recipe, foreign_key

from apps.catalog.tests.baker_recipes import treatment
from apps.pricing.models import TreatmentPackage
from apps.providers.tests.baker_recipes import hospital

package = Recipe(
    TreatmentPackage,
    treatment=foreign_key(treatment),
    hospital=foreign_key(hospital),
    price_min_inr=250_000,
    price_max_inr=None,
    is_published=True,
)
