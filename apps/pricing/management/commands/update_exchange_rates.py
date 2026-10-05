from django.core.management.base import BaseCommand, CommandError

from apps.pricing.exchange_rates import ExchangeRateError
from apps.pricing.services import update_exchange_rates


class Command(BaseCommand):
    help = "Fetch the latest reference exchange rates (run once a day)."

    def handle(self, *args, **options):
        try:
            rates = update_exchange_rates()
        except ExchangeRateError as exc:
            raise CommandError(str(exc)) from exc

        for rate in rates:
            self.stdout.write(f"{rate} (rate date {rate.rate_date})")
        self.stdout.write(self.style.SUCCESS(f"Updated {len(rates)} exchange rates."))
