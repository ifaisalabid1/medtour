from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from health_check.views import HealthCheckView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("staff/leads/", include("apps.leads.urls")),
    # For uptime monitoring: 200 when the database and both storages work.
    path(
        "health/",
        HealthCheckView.as_view(
            checks=[
                "health_check.Database",
                ("health_check.Storage", {"alias": "default"}),
                ("health_check.Storage", {"alias": "private"}),
            ]
        ),
        name="health_check",
    ),
    path("", include("apps.website.urls")),
]

# Serves uploaded files during development only (does nothing when DEBUG=False).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if "debug_toolbar" in settings.INSTALLED_APPS:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
