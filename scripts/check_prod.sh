#!/usr/bin/env bash
# Check that production settings load and pass Django's deployment checks.
# Uses placeholder values, so no real secrets are needed. Run before deploying.
set -euo pipefail
cd "$(dirname "$0")/.."

secret_key="$(uv run python -c 'import secrets; print(secrets.token_urlsafe(50))')"

env \
  DJANGO_SECRET_KEY="$secret_key" \
  DJANGO_ALLOWED_HOSTS=example.com \
  SITE_URL=https://example.com \
  DJANGO_DEFAULT_FROM_EMAIL="Medtour <care@example.com>" \
  ENQUIRY_ALERT_EMAILS=team@example.com \
  TURNSTILE_SITE_KEY=placeholder TURNSTILE_SECRET_KEY=placeholder \
  AWS_SES_ACCESS_KEY_ID=placeholder AWS_SES_SECRET_ACCESS_KEY=placeholder \
  R2_ACCOUNT_ID=placeholder R2_ACCESS_KEY_ID=placeholder R2_SECRET_ACCESS_KEY=placeholder \
  R2_PUBLIC_BUCKET=media R2_PRIVATE_BUCKET=private R2_PUBLIC_DOMAIN=media.example.com \
  uv run python manage.py check --deploy --settings=config.settings.prod
