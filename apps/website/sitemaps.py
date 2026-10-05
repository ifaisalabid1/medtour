"""XML sitemaps, one per page type, so Search Console reports each separately."""

from django.contrib.sitemaps import Sitemap

from apps.catalog.selectors import published_conditions, published_specialities
from apps.content.selectors import published_articles
from apps.locations.selectors import published_source_countries
from apps.providers.selectors import published_doctors, published_hospitals

from .seo import indexable_treatments


class PublicPageSitemap(Sitemap):
    """Lists a selector's pages, with the date each was last edited."""

    def __init__(self, selector):
        super().__init__()
        self.selector = selector

    def items(self):
        # Stable order keeps sitemap pages consistent; dropping the
        # selectors' prefetches avoids loading data the sitemap never shows.
        return self.selector().prefetch_related(None).order_by("pk")

    def lastmod(self, page):
        return page.updated_at


SITEMAPS = {
    "treatments": PublicPageSitemap(indexable_treatments),
    "specialities": PublicPageSitemap(published_specialities),
    "conditions": PublicPageSitemap(published_conditions),
    "hospitals": PublicPageSitemap(published_hospitals),
    "doctors": PublicPageSitemap(published_doctors),
    "medical-travel": PublicPageSitemap(published_source_countries),
    "articles": PublicPageSitemap(published_articles),
}
