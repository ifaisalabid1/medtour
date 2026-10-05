from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import ExchangeRate, TreatmentPackage


@admin.register(TreatmentPackage)
class TreatmentPackageAdmin(ModelAdmin):
    list_display = (
        "treatment",
        "hospital",
        "price_min_inr",
        "price_max_inr",
        "price_updated_on",
        "is_published",
    )
    list_filter = (
        "is_published",
        "treatment__speciality",
        "hospital__city",
        "price_updated_on",
    )
    list_select_related = ("treatment", "hospital__city")
    search_fields = ("treatment__name", "hospital__name")
    autocomplete_fields = ("treatment", "hospital")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("treatment", "hospital", "is_published")}),
        (
            _("Indicative price"),
            {"fields": ("price_min_inr", "price_max_inr", "price_updated_on")},
        ),
        (_("What the price covers"), {"fields": ("inclusions", "exclusions")}),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(ExchangeRate)
class ExchangeRateAdmin(ModelAdmin):
    list_display = ("currency", "inr_per_unit", "rate_date", "updated_at")
    readonly_fields = ("updated_at",)
