from .base import *

# Fast hashing: tests create many users and don't need real password security.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tests don't need the connection pool, and leaving it out keeps the test
# database simple to create and tear down.
DATABASES["default"]["OPTIONS"] = {}

# Keep uploaded test files in memory instead of writing them to disk.
STORAGES = {
    **STORAGES,
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "private": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
}

# Run tasks immediately, in the test process.
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
        "QUEUES": ["default", "emails"],
    }
}

# Collect sent emails in django.core.mail.outbox.
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
SITE_URL = "https://medtour.example"
ENQUIRY_ALERT_EMAILS = ["team@medtour.example"]
