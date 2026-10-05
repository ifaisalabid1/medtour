from django.conf import settings
from django.utils.translation import gettext_lazy as _


def environment_callback(request):
    """Show which environment the admin is connected to, to prevent mistakes."""
    if settings.DEBUG:
        return [_("Development"), "info"]
    return [_("Production"), "danger"]


TIMESTAMPS_FIELDSET = (
    _("Timestamps"),
    {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
)
