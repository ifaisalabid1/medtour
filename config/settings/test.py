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
