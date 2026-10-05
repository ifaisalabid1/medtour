from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

from config.storage import r2_storages

from .base import *


def required(name: str) -> str:
    """A setting that must be present AND non-empty.

    env.str() only fails when a variable is missing. An empty value (say, a
    blank line copied from .env.example) would otherwise switch a feature
    off silently, such as spam protection rejecting every patient.
    """
    value = env.str(name, default="").strip()
    if not value:
        raise ImproperlyConfigured(
            f"Set the {name} environment variable (it is empty)."
        )
    return value


def required_list(name: str) -> list[str]:
    values = [value.strip() for value in env.list(name, default=[]) if value.strip()]
    if not values:
        raise ImproperlyConfigured(
            f"Set the {name} environment variable (it is empty)."
        )
    return values


DEBUG = False
ALLOWED_HOSTS = required_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Behind Cloudflare and a reverse proxy, HTTPS ends before reaching Django.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Start HSTS low and raise it to 31536000 (one year) once HTTPS is confirmed
# working in production.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)

# Real Turnstile keys are mandatory: the test keys accept every submission.
TURNSTILE_SITE_KEY = required("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = required("TURNSTILE_SECRET_KEY")

# Email goes out through Amazon SES in the Mumbai region, via Anymail.
MAILERS = {
    "default": {
        "BACKEND": "anymail.backends.amazon_ses.EmailBackend",
        "OPTIONS": {
            "client_params": {
                "region_name": env.str("AWS_SES_REGION", default="ap-south-1"),
                "aws_access_key_id": required("AWS_SES_ACCESS_KEY_ID"),
                "aws_secret_access_key": required("AWS_SES_SECRET_ACCESS_KEY"),
            },
        },
    },
}
DEFAULT_FROM_EMAIL = required("DJANGO_DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_URL = required("SITE_URL")
ENQUIRY_ALERT_EMAILS = required_list("ENQUIRY_ALERT_EMAILS")

# Uploaded files live in Cloudflare R2: images in a public bucket served from
# your media domain, medical documents in a private bucket.
R2_PUBLIC_DOMAIN = required("R2_PUBLIC_DOMAIN")
STORAGES = {
    **STORAGES,
    **r2_storages(
        account_id=required("R2_ACCOUNT_ID"),
        access_key=required("R2_ACCESS_KEY_ID"),
        secret_key=required("R2_SECRET_ACCESS_KEY"),
        public_bucket=required("R2_PUBLIC_BUCKET"),
        public_domain=R2_PUBLIC_DOMAIN,
        private_bucket=required("R2_PRIVATE_BUCKET"),
    ),
}

# Images are served from the media domain, so the policy must allow it.
_MEDIA_ORIGIN = f"https://{R2_PUBLIC_DOMAIN}"
SECURE_CSP = {**SECURE_CSP, "img-src": [CSP.SELF, _MEDIA_ORIGIN]}
ADMIN_CSP = {**ADMIN_CSP, "img-src": [CSP.SELF, _MEDIA_ORIGIN]}

# Error tracking. Optional: leave SENTRY_DSN unset to disable.
SENTRY_DSN = env.str("SENTRY_DSN", default="").strip()
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env.str("SENTRY_ENVIRONMENT", default="production"),
        # Patient data must never reach a third party in an error report:
        send_default_pii=False,  # no user emails, IP addresses or cookies
        max_request_body_size="never",  # form posts contain medical details
        include_local_variables=False,  # stack frames can hold patient data
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
    )
