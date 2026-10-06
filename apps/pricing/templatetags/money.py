from django import template

from apps.pricing.money import convert_from_inr, format_inr

register = template.Library()


@register.filter
def inr(amount):
    """{{ package.price_min_inr|inr }} -> "₹2,50,000". Empty for no amount."""
    if amount is None or amount == "":
        return ""
    return format_inr(int(amount))


@register.filter
def usd(amount_inr, inr_per_usd):
    """{{ price|usd:usd_rate }} -> "US$3,010". Empty without an amount or a rate,
    so a missing or stale exchange rate simply hides the conversion."""
    if not amount_inr or not inr_per_usd:
        return ""
    return f"US${convert_from_inr(int(amount_inr), inr_per_usd):,}"
