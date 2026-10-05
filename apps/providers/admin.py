from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import Accreditation, Doctor, Hospital, HospitalAccreditation


@admin.register(Accreditation)
class AccreditationAdmin(ModelAdmin):
    list_display = ("abbreviation", "name")
    search_fields = ("abbreviation", "name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("abbreviation", "name", "description")}),
        TIMESTAMPS_FIELDSET,
    )


class HospitalAccreditationInline(TabularInline):
    model = HospitalAccreditation
    extra = 0
    autocomplete_fields = ("accreditation",)
    fields = ("accreditation", "certificate_number", "valid_until")


@admin.register(Hospital)
class HospitalAdmin(ModelAdmin):
    list_display = ("name", "city", "bed_count", "is_published", "updated_at")
    list_filter = ("is_published", "city", "accreditations")
    search_fields = ("name", "also_known_as")
    autocomplete_fields = ("city", "specialities")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = (HospitalAccreditationInline,)
    fieldsets = (
        (None, {"fields": ("name", "slug", "also_known_as", "city", "is_published")}),
        (_("Address"), {"fields": ("address", "postal_code")}),
        (
            _("Profile"),
            {
                "fields": (
                    "summary",
                    "description",
                    "image",
                    "established_year",
                    "bed_count",
                    "specialities",
                )
            },
        ),
        TIMESTAMPS_FIELDSET,
    )

    def get_queryset(self, request):
        # The hospital's name includes its city. Loading the city in the same
        # query keeps the list and the doctor form's hospital picker fast.
        return super().get_queryset(request).select_related("city")


@admin.register(Doctor)
class DoctorAdmin(ModelAdmin):
    list_display = ("__str__", "designation", "practising_since", "is_published")
    list_filter = ("is_published", "specialities", "hospitals")
    search_fields = ("name", "qualifications", "designation")
    autocomplete_fields = ("specialities", "hospitals")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "is_published")}),
        (
            _("Credentials"),
            {
                "fields": (
                    "designation",
                    "qualifications",
                    "practising_since",
                    "medical_registration_number",
                )
            },
        ),
        (_("Profile"), {"fields": ("summary", "description", "photo")}),
        (_("Where they practise"), {"fields": ("hospitals", "specialities")}),
        TIMESTAMPS_FIELDSET,
    )
