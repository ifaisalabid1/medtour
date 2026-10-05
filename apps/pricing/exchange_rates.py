"""Fetch daily reference exchange rates from the Frankfurter API (ECB data)."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import requests

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"
TIMEOUT_SECONDS = 10


class ExchangeRateError(Exception):
    pass


@dataclass(frozen=True)
class RateQuote:
    currency: str
    inr_per_unit: Decimal
    rate_date: date


def fetch_inr_rate(currency: str) -> RateQuote:
    """How many rupees one unit of `currency` buys, per the latest ECB rate."""
    try:
        response = requests.get(
            FRANKFURTER_URL,
            params={"base": currency, "symbols": "INR"},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        # parse_float=Decimal keeps the rate exact instead of a binary float.
        data = response.json(parse_float=Decimal)
        return RateQuote(
            currency=currency,
            inr_per_unit=Decimal(data["rates"]["INR"]),
            rate_date=date.fromisoformat(data["date"]),
        )
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        raise ExchangeRateError(f"Could not fetch the {currency} to INR rate.") from exc
