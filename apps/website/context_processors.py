from django.conf import settings


def site(request):
    """Site name and address, available in every template."""
    return {"SITE_NAME": settings.SITE_NAME, "SITE_URL": settings.SITE_URL}
