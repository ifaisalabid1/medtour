from django.db import transaction

from .exchange_rates import fetch_inr_rate
from .models import DisplayCurrency, ExchangeRate


def update_exchange_rates() -> list[ExchangeRate]:
    """Fetch today's rate for every display currency and save them.

    All rates are fetched before anything is written, so a network failure
    halfway through never leaves a mix of old and new rates. The HTTP calls
    also stay outside the database transaction, which keeps it short.
    """
    quotes = [fetch_inr_rate(currency) for currency in DisplayCurrency.values]

    with transaction.atomic():
        return [
            ExchangeRate.objects.update_or_create(
                currency=quote.currency,
                defaults={
                    "inr_per_unit": quote.inr_per_unit,
                    "rate_date": quote.rate_date,
                },
            )[0]
            for quote in quotes
        ]
