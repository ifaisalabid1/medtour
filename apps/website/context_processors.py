from urllib.parse import quote

from django.conf import settings

WHATSAPP_GREETING = "Hello, I would like help with treatment in India."


def site(request):
    """Site name, address and contact details, available in every template."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "CONTACT_PHONE": settings.CONTACT_PHONE,
        "CONTACT_EMAIL": settings.CONTACT_EMAIL,
        "WHATSAPP_URL": (
            f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(WHATSAPP_GREETING)}"
        ),
    }
