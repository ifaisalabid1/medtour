from decimal import Decimal

from django.template import Context, Template


def render(template, **context):
    return Template("{% load money %}" + template).render(Context(context))


def test_inr_filter_formats_rupees():
    assert render("{{ amount|inr }}", amount=250000) == "₹2,50,000"


def test_inr_filter_is_empty_without_an_amount():
    assert render("{{ amount|inr }}", amount=None) == ""


def test_usd_filter_converts_rupees_at_the_given_rate():
    rendered = render("{{ amount|usd:rate }}", amount=250000, rate=Decimal("83.10"))

    assert rendered == "US$3,010"


def test_usd_filter_is_empty_without_a_rate():
    assert render("{{ amount|usd:rate }}", amount=250000, rate=None) == ""
