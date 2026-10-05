from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import ConsentRecord, Enquiry, EnquiryDocument

PATIENT_FIELDS = (
    "full_name",
    "email",
    "phone",
    "prefers_whatsapp",
    "country",
    "patient_age",
    "treatment",
    "hospital",
    "doctor",
    "message",
)
TRACKING_FIELDS = (
    "landing_page",
    "referrer",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
)


class ReadOnlyInline(TabularInline):
    """Evidence (documents, consent) is shown to staff but never edited."""

    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class EnquiryDocumentInline(ReadOnlyInline):
    model = EnquiryDocument
    fields = ("original_name", "uploaded_at", "download")
    readonly_fields = fields

    @admin.display(description=_("file"))
    def download(self, document):
        url = reverse("leads:download_document", args=[document.pk])
        return format_html('<a href="{}">{}</a>', url, _("Download"))


class ConsentRecordInline(ReadOnlyInline):
    model = ConsentRecord
    fields = (
        "purpose",
        "consent_text_version",
        "consent_text",
        "granted_at",
        "ip_address",
        "withdrawn_at",
    )
    readonly_fields = fields


@admin.register(Enquiry)
class EnquiryAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = (
        "reference",
        "full_name",
        "country",
        "treatment",
        "status",
        "assigned_to",
        "created_at",
    )
    list_editable = ("status", "assigned_to")
    list_filter = ("status", "assigned_to", "country", "treatment", "utm_source")
    list_select_related = ("treatment", "assigned_to")
    search_fields = ("reference", "full_name", "email", "phone")
    date_hierarchy = "created_at"
    autocomplete_fields = ("treatment", "hospital", "doctor")
    # Contact details stay editable (patients mistype numbers); every change
    # is kept in the history. What the patient wrote and where they came from
    # are evidence, so they're read-only.
    readonly_fields = (
        "reference",
        "message",
        *TRACKING_FIELDS,
        "created_at",
        "updated_at",
    )
    inlines = (EnquiryDocumentInline, ConsentRecordInline)
    actions = ("assign_to_me",)
    fieldsets = (
        (
            _("Case"),
            {"fields": ("reference", "status", "assigned_to", "internal_notes")},
        ),
        (_("Patient"), {"fields": PATIENT_FIELDS}),
        (
            _("Lead source"),
            {"fields": TRACKING_FIELDS, "classes": ("collapse",)},
        ),
        TIMESTAMPS_FIELDSET,
    )

    def has_add_permission(self, request):
        # Enquiries only come from the website, with consent attached.
        return False

    def has_delete_permission(self, request, obj=None):
        # Deleting is for data-erasure requests only.
        return request.user.is_superuser

    @admin.action(description=_("Assign selected enquiries to me"))
    def assign_to_me(self, request, queryset):
        updated = 0
        for enquiry in queryset:
            # Saving one by one records each change in the history.
            enquiry.assigned_to = request.user
            enquiry.save(update_fields=["assigned_to", "updated_at"])
            updated += 1
        self.message_user(
            request, _("%(count)d enquiries assigned to you.") % {"count": updated}
        )
