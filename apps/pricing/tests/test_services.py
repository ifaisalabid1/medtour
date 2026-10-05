from datetime import date
from decimal import Decimal

import pytest
from django.core.management import CommandError, call_command

from apps.pricing import services
from apps.pricing.exchange_rates import ExchangeRateError, RateQuote
from apps.pricing.models import ExchangeRate

pytestmark = pytest.mark.django_db

FAKE_RATES = {"USD": "96.32", "EUR": "108.10", "GBP": "127.20"}


def fake_fetch(currency):
    return RateQuote(currency, Decimal(FAKE_RATES[currency]), date(2026, 10, 2))


def test_update_exchange_rates_saves_every_display_currency(monkeypatch):
    monkeypatch.setattr(services, "fetch_inr_rate", fake_fetch)

    services.update_exchange_rates()
    services.update_exchange_rates()  # running twice must not duplicate rows

    saved = dict(ExchangeRate.objects.values_list("currency", "inr_per_unit"))
    assert saved == {code: Decimal(rate) for code, rate in FAKE_RATES.items()}


def test_a_failed_fetch_leaves_existing_rates_untouched(monkeypatch):
    ExchangeRate.objects.create(
        currency="USD", inr_per_unit=Decimal("95"), rate_date=date(2026, 10, 1)
    )

    def flaky_fetch(currency):
        if currency == "GBP":
            raise ExchangeRateError("GBP failed")
        return fake_fetch(currency)

    monkeypatch.setattr(services, "fetch_inr_rate", flaky_fetch)

    with pytest.raises(ExchangeRateError):
        services.update_exchange_rates()

    assert ExchangeRate.objects.get().inr_per_unit == Decimal("95")


def test_command_reports_the_updated_rates(monkeypatch, capsys):
    monkeypatch.setattr(services, "fetch_inr_rate", fake_fetch)

    call_command("update_exchange_rates")

    assert "Updated 3 exchange rates." in capsys.readouterr().out


def test_command_fails_clearly_when_the_api_is_down(monkeypatch):
    def failing_fetch(currency):
        raise ExchangeRateError("Could not fetch the USD to INR rate.")

    monkeypatch.setattr(services, "fetch_inr_rate", failing_fetch)

    with pytest.raises(CommandError, match="Could not fetch"):
        call_command("update_exchange_rates")
