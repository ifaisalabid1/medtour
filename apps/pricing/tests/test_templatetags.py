from django.template import Context, Template


def render(template, **context):
    return Template("{% load money %}" + template).render(Context(context))


def test_inr_filter_formats_rupees():
    assert render("{{ amount|inr }}", amount=250000) == "₹2,50,000"


def test_inr_filter_is_empty_without_an_amount():
    assert render("{{ amount|inr }}", amount=None) == ""
