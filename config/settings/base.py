"""Settings shared by every environment. Environment files import from here."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

# In production, variables come from the process environment (systemd/Docker),
# so a missing .env file is expected there.
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    env.read_env(ENV_FILE)

# --- Core --------------------------------------------------------------------

SECRET_KEY = env.str("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS: list[str] = env.list("DJANGO_ALLOWED_HOSTS", default=[])
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="admin/")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# --- Applications ------------------------------------------------------------

UNFOLD_APPS = [
    "unfold",  # must come before django.contrib.admin
    "unfold.contrib.simple_history",
]
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]
THIRD_PARTY_APPS = [
    "django_countries",
    "django_prose_editor",
    "phonenumber_field",
    "simple_history",
]
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.locations",
    "apps.catalog",
    "apps.providers",
    "apps.pricing",
    "apps.content",
    "apps.leads",
]

INSTALLED_APPS = UNFOLD_APPS + DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ----------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("POSTGRES_DB"),
        "USER": env.str("POSTGRES_USER"),
        "PASSWORD": env.str("POSTGRES_PASSWORD"),
        "HOST": env.str("POSTGRES_HOST", default="localhost"),
        "PORT": env.int("POSTGRES_PORT", default=5432),
        # psycopg 3 connection pool (Django 5.1+). Don't combine with CONN_MAX_AGE.
        "OPTIONS": {"pool": True},
    }
}

AUTH_USER_MODEL = "accounts.User"

# --- Authentication ----------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # Staff accounts can see patient data, so require longer passwords.
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalisation ----------------------------------------------------

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# --- Static files ------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# --- Uploaded files ----------------------------------------------------------

# Local disk for development. Production switches to Cloudflare R2 in Step 10.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Medical reports. Outside MEDIA_ROOT, so no URL ever serves them.
    "private": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": BASE_DIR / "private_media"},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# --- Phone numbers -----------------------------------------------------------

# Numbers typed without a country code are treated as Indian.
PHONENUMBER_DEFAULT_REGION = "IN"

# --- Cloudflare Turnstile (spam protection on public forms) -----------------

# Defaults are Cloudflare's official test keys, which always pass.
# Production must set real keys (prod.py requires them).
TURNSTILE_SITE_KEY = env.str("TURNSTILE_SITE_KEY", default="1x00000000000000000000AA")
TURNSTILE_SECRET_KEY = env.str(
    "TURNSTILE_SECRET_KEY", default="1x0000000000000000000000000000000AA"
)

# --- Logging -----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# --- Admin (Unfold) ----------------------------------------------------------

UNFOLD = {
    "SITE_TITLE": "Medtour Admin",
    "SITE_HEADER": "Medtour",
    "SITE_SYMBOL": "health_and_safety",  # Material Symbols icon name
    "ENVIRONMENT": "apps.core.admin_config.environment_callback",
}
