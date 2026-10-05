from config.storage import r2_storages

from .base import *

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # no default: fail loudly if unset
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
TURNSTILE_SITE_KEY = env.str("TURNSTILE_SITE_KEY")
TURNSTILE_SECRET_KEY = env.str("TURNSTILE_SECRET_KEY")

# Email goes out through Amazon SES in the Mumbai region, via Anymail.
MAILERS = {
    "default": {
        "BACKEND": "anymail.backends.amazon_ses.EmailBackend",
        "OPTIONS": {
            "client_params": {
                "region_name": env.str("AWS_SES_REGION", default="ap-south-1"),
                "aws_access_key_id": env.str("AWS_SES_ACCESS_KEY_ID"),
                "aws_secret_access_key": env.str("AWS_SES_SECRET_ACCESS_KEY"),
            },
        },
    },
}
DEFAULT_FROM_EMAIL = env.str("DJANGO_DEFAULT_FROM_EMAIL")
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_URL = env.str("SITE_URL")
ENQUIRY_ALERT_EMAILS = env.list("ENQUIRY_ALERT_EMAILS")

# Uploaded files live in Cloudflare R2: images in a public bucket served from
# your media domain, medical documents in a private bucket.
STORAGES = {
    **STORAGES,
    **r2_storages(
        account_id=env.str("R2_ACCOUNT_ID"),
        access_key=env.str("R2_ACCESS_KEY_ID"),
        secret_key=env.str("R2_SECRET_ACCESS_KEY"),
        public_bucket=env.str("R2_PUBLIC_BUCKET"),
        public_domain=env.str("R2_PUBLIC_DOMAIN"),
        private_bucket=env.str("R2_PRIVATE_BUCKET"),
    ),
}
