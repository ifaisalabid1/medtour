from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

SLUG_HELP_TEXT = _("Used in page URLs. Changing it breaks existing links.")
ALSO_KNOWN_AS_HELP_TEXT = _(
    "Other names and abbreviations patients search for, comma separated. "
    "Example: TKR, knee arthroplasty."
)
SUMMARY_HELP_TEXT = _(
    "One or two plain sentences. Shown on listing cards and used as the "
    "default search-engine description."
)


class TimeStampedModel(models.Model):
    """Adds created/updated timestamps. Every domain model inherits this."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


class PublishableQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True)


class PublishableModel(models.Model):
    """Content editors can hide from the public site without deleting it.

    Defaults to unpublished: medical content must be reviewed before it goes live.
    """

    is_published = models.BooleanField(_("published"), default=False)

    objects = PublishableQuerySet.as_manager()

    class Meta:
        abstract = True


class SlugRedirect(TimeStampedModel):
    """An old slug that should permanently redirect to a page's current URL.

    Created automatically when an editor changes a slug, so links from Google,
    WhatsApp shares and other websites keep working (see core/redirects.py).
    """

    content_type = models.ForeignKey(
        ContentType, verbose_name=_("page type"), on_delete=models.CASCADE
    )
    object_id = models.PositiveBigIntegerField(_("page id"))
    old_slug = models.SlugField(_("old slug"), max_length=200)

    class Meta:
        verbose_name = _("slug redirect")
        verbose_name_plural = _("slug redirects")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "old_slug"],
                name="core_slugredirect_unique_old_slug",
            ),
        ]

    def __str__(self):
        return f"{self.content_type.model}: {self.old_slug}"
