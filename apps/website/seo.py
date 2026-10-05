"""Which pages are worth showing to search engines.

A programmatic page with nothing unique on it ("thin content") hurts the
whole site's ranking, so treatment pages stay out of search results until
they have real substance.
"""

from django.db.models import Exists, OuterRef, QuerySet
from django.utils.html import strip_tags
from django.utils.text import Truncator

from apps.catalog.models import Treatment
from apps.catalog.selectors import published_treatments
from apps.content.models import FAQ
from apps.pricing.selectors import published_packages


def indexable_treatments() -> QuerySet[Treatment]:
    """Published treatments with at least one public price and one FAQ.

    This is the single definition of "enough content": the sitemap lists
    these, and every other treatment page is marked noindex.
    """
    has_public_price = Exists(published_packages().filter(treatment=OuterRef("pk")))
    has_faq = Exists(FAQ.objects.published().filter(treatment=OuterRef("pk")))
    return published_treatments().filter(has_public_price, has_faq)


def is_indexable(treatment: Treatment) -> bool:
    return indexable_treatments().filter(pk=treatment.pk).exists()


META_DESCRIPTION_LENGTH = 160


def meta_description(*candidates: str) -> str:
    """The first non-empty text, as plain text of at most 160 characters.

    Search engines show about this much. Rich text is stripped of HTML, and
    an empty result means the page simply has no description tag.
    """
    for text in candidates:
        plain = " ".join(strip_tags(text or "").split())
        if plain:
            return Truncator(plain).chars(META_DESCRIPTION_LENGTH)
    return ""
