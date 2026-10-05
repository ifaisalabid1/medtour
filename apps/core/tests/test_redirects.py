import pytest
from django.http import Http404
from model_bakery import baker

from apps.catalog.models import Treatment
from apps.catalog.selectors import published_treatments
from apps.core.models import SlugRedirect
from apps.core.redirects import RedirectToCurrentURL, get_object_or_redirect

pytestmark = pytest.mark.django_db


def make_treatment(**fields):
    return baker.make_recipe(
        "apps.catalog.tests.treatment", name="Knee replacement", slug="knee", **fields
    )


def rename(treatment, slug):
    treatment.slug = slug
    treatment.save()


def test_changing_a_slug_records_a_redirect():
    treatment = make_treatment()

    rename(treatment, "knee-replacement")

    redirect = SlugRedirect.objects.get()
    assert redirect.old_slug == "knee"
    assert redirect.object_id == treatment.pk


def test_saving_without_a_slug_change_records_nothing():
    treatment = make_treatment()

    treatment.summary = "Updated summary"
    treatment.save()

    assert not SlugRedirect.objects.exists()


def test_old_slug_raises_a_redirect_to_the_current_url():
    treatment = make_treatment()
    rename(treatment, "knee-replacement")

    with pytest.raises(RedirectToCurrentURL) as redirect:
        get_object_or_redirect(published_treatments(), "knee")

    assert redirect.value.url == "/treatments/knee-replacement-cost-in-india/"


def test_every_old_slug_in_a_chain_points_to_the_current_page():
    treatment = make_treatment()
    rename(treatment, "knee-replacement")
    rename(treatment, "total-knee-replacement")

    for old_slug in ("knee", "knee-replacement"):
        with pytest.raises(RedirectToCurrentURL) as redirect:
            get_object_or_redirect(published_treatments(), old_slug)
        assert "total-knee-replacement" in redirect.value.url


def test_going_back_to_an_old_slug_removes_its_redirect():
    treatment = make_treatment()
    rename(treatment, "knee-replacement")
    rename(treatment, "knee")

    assert get_object_or_redirect(published_treatments(), "knee") == treatment
    assert list(SlugRedirect.objects.values_list("old_slug", flat=True)) == [
        "knee-replacement"
    ]


def test_no_redirect_to_an_unpublished_page():
    treatment = make_treatment()
    rename(treatment, "knee-replacement")
    Treatment.objects.filter(pk=treatment.pk).update(is_published=False)

    with pytest.raises(Http404):
        get_object_or_redirect(published_treatments(), "knee")


def test_deleting_a_page_removes_its_redirects():
    treatment = make_treatment()
    rename(treatment, "knee-replacement")

    treatment.delete()

    assert not SlugRedirect.objects.exists()


def test_unknown_slug_is_a_404():
    with pytest.raises(Http404):
        get_object_or_redirect(published_treatments(), "does-not-exist")
