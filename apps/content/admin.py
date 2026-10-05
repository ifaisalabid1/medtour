from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.core.admin_config import TIMESTAMPS_FIELDSET

from .models import FAQ, Article, Author, Testimonial


@admin.register(Author)
class AuthorAdmin(ModelAdmin):
    list_display = ("name", "credentials", "is_medical_professional")
    list_filter = ("is_medical_professional",)
    search_fields = ("name", "credentials")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "credentials", "bio", "photo")}),
        (
            _("Medical credentials"),
            {"fields": ("is_medical_professional", "medical_registration_number")},
        ),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(Article)
class ArticleAdmin(ModelAdmin):
    list_display = (
        "title",
        "author",
        "medical_reviewer",
        "reviewed_on",
        "is_published",
        "published_at",
    )
    list_filter = ("is_published", "medical_reviewer")
    list_select_related = ("author", "medical_reviewer")
    search_fields = ("title", "summary")
    autocomplete_fields = ("author", "medical_reviewer", "treatments", "conditions")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("published_at", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "summary", "cover_image", "body")}),
        (
            _("Authorship and medical review"),
            {"fields": ("author", "medical_reviewer", "reviewed_on")},
        ),
        (_("Related pages"), {"fields": ("treatments", "conditions")}),
        (_("Publishing"), {"fields": ("is_published", "published_at")}),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = (
        "question",
        "treatment",
        "condition",
        "display_order",
        "is_published",
    )
    list_editable = ("display_order",)
    list_filter = ("is_published", "treatment", "condition")
    list_select_related = ("treatment", "condition")
    search_fields = ("question",)
    autocomplete_fields = ("treatment", "condition")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("question", "answer")}),
        (
            _("Shown on"),
            {
                "fields": ("treatment", "condition", "display_order", "is_published"),
                "description": _("Choose a treatment or a condition, not both."),
            },
        ),
        TIMESTAMPS_FIELDSET,
    )


@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display = (
        "patient_display_name",
        "country",
        "treatment",
        "hospital",
        "consent_obtained_on",
        "is_published",
    )
    list_filter = ("is_published", "country", "treatment")
    list_select_related = ("treatment", "hospital__city")
    search_fields = ("patient_display_name", "quote")
    autocomplete_fields = ("treatment", "hospital", "doctor")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("patient_display_name", "country", "quote", "video_url")}),
        (_("Treatment"), {"fields": ("treatment", "hospital", "doctor", "treated_on")}),
        (
            _("Consent (required before publishing)"),
            {"fields": ("consent_obtained_on", "consent_reference", "is_published")},
        ),
        TIMESTAMPS_FIELDSET,
    )
