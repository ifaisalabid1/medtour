from django.db import models
from django.utils.translation import gettext_lazy as _

SLUG_HELP_TEXT = _("Used in page URLs. Changing it breaks existing links.")


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
