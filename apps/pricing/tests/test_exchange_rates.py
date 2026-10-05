from datetime import date
from decimal import Decimal

import pytest
import requests

from apps.pricing import exchange_rates
from apps.pricing.exchange_rates import ExchangeRateError, fetch_inr_rate


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self, **kwargs):
        return self.payload


def test_fetch_inr_rate_parses_the_api_response(monkeypatch):
    calls = []

    def fake_get(url, params, timeout):
        calls.append(params)
        return FakeResponse(
            {"base": "USD", "date": "2026-10-02", "rates": {"INR": Decimal("96.32")}}
        )

    monkeypatch.setattr(exchange_rates.requests, "get", fake_get)

    quote = fetch_inr_rate("USD")

    assert quote.inr_per_unit == Decimal("96.32")
    assert quote.rate_date == date(2026, 10, 2)
    assert calls == [{"base": "USD", "symbols": "INR"}]


def test_network_errors_become_exchange_rate_errors(monkeypatch):
    def failing_get(*args, **kwargs):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(exchange_rates.requests, "get", failing_get)

    with pytest.raises(ExchangeRateError, match="USD"):
        fetch_inr_rate("USD")


def test_unexpected_responses_become_exchange_rate_errors(monkeypatch):
    monkeypatch.setattr(
        exchange_rates.requests, "get", lambda *a, **kw: FakeResponse({"error": "x"})
    )

    with pytest.raises(ExchangeRateError):
        fetch_inr_rate("USD")
