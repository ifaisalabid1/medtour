from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import Condition, Speciality, Treatment


@admin.register(Speciality)
class SpecialityAdmin(ModelAdmin):
    list_display = ("name", "display_order", "is_published", "updated_at")
    list_editable = ("display_order",)
    list_filter = ("is_published",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "display_order", "is_published")}),
        (_("Content"), {"fields": ("summary", "description")}),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(Treatment)
class TreatmentAdmin(ModelAdmin):
    list_display = ("name", "speciality", "is_published", "updated_at")
    list_filter = ("is_published", "speciality")
    list_select_related = ("speciality",)
    search_fields = ("name", "also_known_as")
    autocomplete_fields = ("speciality",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {"fields": ("speciality", "name", "slug", "also_known_as", "is_published")},
        ),
        (_("Content"), {"fields": ("summary", "description")}),
        (
            _("Patient journey"),
            {"fields": ("hospital_stay_days", "stay_in_india_days")},
        ),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(Condition)
class ConditionAdmin(ModelAdmin):
    list_display = ("name", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("name", "also_known_as")
    autocomplete_fields = ("treatments",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "also_known_as", "is_published")}),
        (_("Content"), {"fields": ("summary", "description")}),
        (_("Treatments"), {"fields": ("treatments",)}),
        TIMESTAMPS_FIELDSET,
    )
