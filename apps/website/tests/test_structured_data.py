import pytest
from django.utils import timezone
from model_bakery import baker

from apps.providers.selectors import published_doctors
from apps.website import structured_data as schema

pytestmark = pytest.mark.django_db

SITE = "https://medtour.example"


def test_breadcrumbs_are_numbered_with_absolute_urls():
    data = schema.breadcrumbs(("Home", "/"), ("Orthopaedics", "/specialities/ortho/"))

    assert data["@type"] == "BreadcrumbList"
    assert [item["position"] for item in data["itemListElement"]] == [1, 2]
    assert data["itemListElement"][1]["item"] == f"{SITE}/specialities/ortho/"


def test_medical_procedure_lists_alternative_names():
    treatment = baker.make_recipe(
        "apps.catalog.tests.treatment",
        name="Total Knee Replacement",
        slug="tkr",
        summary="Replaces a worn knee joint.",
        also_known_as="TKR, knee arthroplasty, ",
    )

    data = schema.medical_procedure(treatment)

    assert data["@type"] == "MedicalProcedure"
    assert data["url"] == f"{SITE}/treatments/tkr-cost-in-india/"
    assert data["alternateName"] == ["TKR", "knee arthroplasty"]
    assert "offers" not in data  # MedicalProcedure has no price property


def test_optional_properties_are_left_out_when_empty():
    treatment = baker.make_recipe("apps.catalog.tests.treatment", summary="")

    data = schema.medical_procedure(treatment)

    assert "description" not in data
    assert "alternateName" not in data


def test_faq_page_is_none_without_faqs():
    assert schema.faq_page([]) is None


def test_faq_page_has_one_question_per_faq():
    faq = baker.make_recipe(
        "apps.content.tests.faq",
        question="How long is recovery?",
        answer="<p>About 6 weeks.</p>",
    )

    data = schema.faq_page([faq])

    [question] = data["mainEntity"]
    assert question["name"] == "How long is recovery?"
    assert question["acceptedAnswer"]["text"] == "<p>About 6 weeks.</p>"


def test_hospital_has_an_indian_postal_address():
    city = baker.make_recipe(
        "apps.locations.tests.city", name="Chennai", state="Tamil Nadu"
    )
    hospital = baker.make_recipe(
        "apps.providers.tests.hospital",
        city=city,
        slug="apollo",
        address="21 Greams Lane",
        postal_code="600006",
        established_year=1983,
    )

    data = schema.hospital(hospital)

    assert data["address"] == {
        "@type": "PostalAddress",
        "addressLocality": "Chennai",
        "addressRegion": "Tamil Nadu",
        "addressCountry": "IN",
        "streetAddress": "21 Greams Lane",
        "postalCode": "600006",
    }
    assert data["foundingDate"] == "1983"
    assert "image" not in data


def test_physician_lists_only_public_hospitals():
    public = baker.make_recipe("apps.providers.tests.hospital", name="Public Hospital")
    hidden = baker.make_recipe(
        "apps.providers.tests.hospital", name="Hidden Hospital", is_published=False
    )
    doctor = baker.make_recipe("apps.providers.tests.doctor", name="Asha Rao")
    doctor.hospitals.add(public, hidden)

    data = schema.physician(published_doctors().get())

    assert data["@type"] == "IndividualPhysician"
    assert data["name"] == "Dr. Asha Rao"
    assert [h["name"] for h in data["hospitalAffiliation"]] == ["Public Hospital"]


def test_article_names_its_medical_reviewer_and_review_date():
    reviewer = baker.make_recipe(
        "apps.content.tests.medical_reviewer", name="Dr. Meera Iyer"
    )
    article = baker.make_recipe(
        "apps.content.tests.article",
        medical_reviewer=reviewer,
        reviewed_on=timezone.localdate(),
    )

    data = schema.medical_web_page(article)

    assert data["@type"] == "MedicalWebPage"
    assert data["reviewedBy"] == {"@type": "Person", "name": "Dr. Meera Iyer"}
    assert data["lastReviewed"] == timezone.localdate().isoformat()
    assert data["datePublished"] == article.published_at.isoformat()


def test_organization_and_website_name_the_site(settings):
    settings.SITE_NAME = "Medtour"
    settings.CONTACT_EMAIL = "care@medtour.example"

    organization = schema.organization()

    assert organization["@type"] == "Organization"
    assert organization["url"] == f"{SITE}/"
    assert organization["email"] == "care@medtour.example"
    assert schema.website() == {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Medtour",
        "url": f"{SITE}/",
    }
