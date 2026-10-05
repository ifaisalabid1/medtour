from django.core.files.storage import storages


def private_storage():
    """Storage for files that must never be publicly reachable (medical reports).

    Configured as STORAGES["private"]. Files are only served to staff through
    a permission-checked view, never by URL.
    """
    return storages["private"]
