from django import template

from apps.pricing.money import format_inr

register = template.Library()


@register.filter
def inr(amount):
    """{{ package.price_min_inr|inr }} -> "₹2,50,000". Empty for no amount."""
    if amount is None or amount == "":
        return ""
    return format_inr(int(amount))
