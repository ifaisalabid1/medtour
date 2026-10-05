"""Production settings must refuse to start with a missing or empty secret."""

import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRODUCTION_ENV = {
    "DJANGO_SETTINGS_MODULE": "config.settings.prod",
    "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
    "DJANGO_ALLOWED_HOSTS": "example.com",
    "SITE_URL": "https://example.com",
    "DJANGO_DEFAULT_FROM_EMAIL": "Medtour <care@example.com>",
    "ENQUIRY_ALERT_EMAILS": "team@example.com",
    "TURNSTILE_SITE_KEY": "placeholder",
    "TURNSTILE_SECRET_KEY": "placeholder",
    "AWS_SES_ACCESS_KEY_ID": "placeholder",
    "AWS_SES_SECRET_ACCESS_KEY": "placeholder",
    "R2_ACCOUNT_ID": "placeholder",
    "R2_ACCESS_KEY_ID": "placeholder",
    "R2_SECRET_ACCESS_KEY": "placeholder",
    "R2_PUBLIC_BUCKET": "media",
    "R2_PRIVATE_BUCKET": "private",
    "R2_PUBLIC_DOMAIN": "media.example.com",
}


def run_check(**overrides):
    env = {**os.environ, **PRODUCTION_ENV, **overrides}
    return subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_settings_load_with_every_value_set():
    result = run_check()

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "name", ["TURNSTILE_SECRET_KEY", "R2_PRIVATE_BUCKET", "ENQUIRY_ALERT_EMAILS"]
)
def test_an_empty_required_value_stops_production_from_starting(name):
    result = run_check(**{name: "  "})

    assert result.returncode != 0
    assert f"Set the {name} environment variable (it is empty)." in result.stderr
