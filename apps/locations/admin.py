from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import City, SourceCountry


@admin.register(City)
class CityAdmin(ModelAdmin):
    list_display = ("name", "state", "slug", "is_published", "updated_at")
    list_filter = ("is_published", "state")
    search_fields = ("name", "state")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "state", "is_published")}),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(SourceCountry)
class SourceCountryAdmin(ModelAdmin):
    list_display = ("country", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("slug",)  # the country column stores a code, so search by slug
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("country", "slug", "is_published")}),
        (_("Content"), {"fields": ("intro", "visa_info")}),
        TIMESTAMPS_FIELDSET,
    )
