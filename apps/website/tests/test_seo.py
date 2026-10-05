import json
import re

import pytest
from django.urls import reverse
from model_bakery import baker

from apps.website.seo import indexable_treatments, meta_description

pytestmark = pytest.mark.django_db


@pytest.fixture
def treatment():
    return baker.make_recipe(
        "apps.catalog.tests.treatment",
        name="Knee replacement",
        slug="knee-replacement",
        summary="Replaces a worn knee joint.",
    )


def give_content(treatment):
    baker.make_recipe("apps.pricing.tests.package", treatment=treatment)
    baker.make_recipe("apps.content.tests.faq", treatment=treatment)


def structured_data(response):
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', response.text
    )
    return [json.loads(block) for block in blocks]


# --- Thin content --------------------------------------------------------------


def test_treatment_needs_a_price_and_an_faq_to_be_indexable(treatment):
    assert list(indexable_treatments()) == []

    baker.make_recipe("apps.pricing.tests.package", treatment=treatment)
    assert list(indexable_treatments()) == []  # price only

    baker.make_recipe("apps.content.tests.faq", treatment=treatment)
    assert list(indexable_treatments()) == [treatment]


def test_unpublished_prices_and_faqs_do_not_count(treatment):
    baker.make_recipe(
        "apps.pricing.tests.package", treatment=treatment, is_published=False
    )
    baker.make_recipe("apps.content.tests.faq", treatment=treatment, is_published=False)

    assert list(indexable_treatments()) == []


def test_thin_treatment_page_is_marked_noindex(client, treatment):
    response = client.get(treatment.get_absolute_url())

    assert '<meta name="robots" content="noindex, follow">' in response.text


def test_treatment_page_with_content_can_be_indexed(client, treatment):
    give_content(treatment)

    response = client.get(treatment.get_absolute_url())

    assert 'name="robots"' not in response.text


# --- Head tags and structured data ---------------------------------------------


def test_page_has_title_description_and_canonical_url(client, treatment):
    response = client.get(treatment.get_absolute_url() + "?utm_source=google")

    assert "<title>Knee replacement cost in India | Medtour</title>" in response.text
    assert '<meta name="description" content="Replaces a worn knee joint.">' in (
        response.text
    )
    # The canonical URL ignores tracking parameters.
    assert (
        '<link rel="canonical" '
        'href="https://medtour.example/treatments/knee-replacement-cost-in-india/">'
    ) in response.text


def test_meta_description_is_plain_text_and_at_most_160_characters():
    text = meta_description("<p>Knee   replacement " + "detail " * 40 + "</p>")

    assert "<p>" not in text
    assert "  " not in text
    assert len(text) <= 160


def test_meta_description_uses_the_first_non_empty_candidate():
    assert meta_description("", "  ", "<p></p>", "Fallback text") == "Fallback text"
    assert meta_description("", "") == ""


def test_treatment_without_a_summary_gets_a_factual_fallback(client, treatment):
    treatment.summary = ""
    treatment.save()

    response = client.get(treatment.get_absolute_url())

    assert (
        '<meta name="description" content="Indicative cost of Knee replacement in '
        'India, with prices from partner hospitals.">'
    ) in response.text


def test_no_empty_description_tag(client):
    hospital = baker.make_recipe("apps.providers.tests.hospital", summary="")

    response = client.get(hospital.get_absolute_url())

    assert 'name="description"' not in response.text


def test_treatment_page_structured_data(client, treatment):
    give_content(treatment)

    types = [
        block["@type"]
        for block in structured_data(client.get(treatment.get_absolute_url()))
    ]

    assert types == ["MedicalProcedure", "FAQPage", "BreadcrumbList"]


def test_no_faq_markup_without_faqs(client, treatment):
    types = [
        block["@type"]
        for block in structured_data(client.get(treatment.get_absolute_url()))
    ]

    assert "FAQPage" not in types


# --- Sitemaps and robots.txt ---------------------------------------------------


def test_sitemap_index_lists_every_section(client):
    response = client.get(reverse("website:sitemap_index"))

    assert response.status_code == 200
    for section in (
        "treatments",
        "specialities",
        "conditions",
        "hospitals",
        "doctors",
        "medical-travel",
        "articles",
    ):
        assert f"/sitemap-{section}.xml" in response.text


def test_treatment_sitemap_lists_only_indexable_treatments(client, treatment):
    thin = baker.make_recipe("apps.catalog.tests.treatment", slug="thin-page")
    give_content(treatment)

    response = client.get(
        reverse("website:sitemap_section", kwargs={"section": "treatments"})
    )

    assert treatment.get_absolute_url() in response.text
    assert thin.get_absolute_url() not in response.text
    assert "<lastmod>" in response.text


def test_hospital_sitemap_lists_only_published_hospitals(client):
    visible = baker.make_recipe("apps.providers.tests.hospital", slug="visible")
    hidden = baker.make_recipe(
        "apps.providers.tests.hospital", slug="hidden", is_published=False
    )

    response = client.get(
        reverse("website:sitemap_section", kwargs={"section": "hospitals"})
    )

    assert visible.get_absolute_url() in response.text
    assert hidden.get_absolute_url() not in response.text


def test_robots_txt_points_to_the_sitemap_and_hides_staff_pages(client, settings):
    response = client.get("/robots.txt")

    assert response["Content-Type"] == "text/plain"
    assert "Disallow: /staff/" in response.text
    assert "Sitemap: https://medtour.example/sitemap.xml" in response.text
    assert settings.ADMIN_URL not in response.text
