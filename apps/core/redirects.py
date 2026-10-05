"""Keep old URLs working when an editor changes a page's slug.

Changing a slug changes the page's address. Without a redirect, every link
to the old address (Google results, WhatsApp shares, other websites) breaks
and the page loses its search ranking.
"""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, QuerySet
from django.db.models.signals import post_delete, pre_save
from django.http import Http404, HttpResponsePermanentRedirect

from .models import PublishableModel, SlugRedirect


def connect_slug_tracking() -> None:
    """Track slug changes on every public page model (publishable + slug)."""
    for model in apps.get_models():
        if issubclass(model, PublishableModel) and _has_slug(model):
            pre_save.connect(
                _record_slug_change,
                sender=model,
                dispatch_uid=f"slug-redirect-{model._meta.label}",
            )
            post_delete.connect(
                _forget_redirects,
                sender=model,
                dispatch_uid=f"slug-redirect-delete-{model._meta.label}",
            )


def _has_slug(model) -> bool:
    return any(field.name == "slug" for field in model._meta.concrete_fields)


def _record_slug_change(sender, instance, raw=False, **kwargs) -> None:
    if raw or instance._state.adding:
        return
    old_slug = (
        sender._base_manager.filter(pk=instance.pk)
        .values_list("slug", flat=True)
        .first()
    )
    if old_slug is None or old_slug == instance.slug:
        return
    content_type = ContentType.objects.get_for_model(sender)
    SlugRedirect.objects.update_or_create(
        content_type=content_type,
        old_slug=old_slug,
        defaults={"object_id": instance.pk},
    )
    # If the new slug was itself an old slug, it's live again: drop that
    # redirect so it can't send visitors away from the page.
    SlugRedirect.objects.filter(
        content_type=content_type, old_slug=instance.slug
    ).delete()


def _forget_redirects(sender, instance, **kwargs) -> None:
    SlugRedirect.objects.filter(
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.pk,
    ).delete()


def get_object_or_redirect(queryset: QuerySet, slug: str) -> Model:
    """Return the page with this slug from `queryset` (normally a selector of
    published pages). Raises RedirectToCurrentURL for an old slug, Http404
    otherwise."""
    page = queryset.filter(slug=slug).first()
    if page is not None:
        return page

    object_id = (
        SlugRedirect.objects.filter(
            content_type=ContentType.objects.get_for_model(queryset.model),
            old_slug=slug,
        )
        .values_list("object_id", flat=True)
        .first()
    )
    # Only redirect to a page the visitor is allowed to see.
    current = queryset.filter(pk=object_id).first() if object_id else None
    if current is None:
        raise Http404
    raise RedirectToCurrentURL(current.get_absolute_url())


class RedirectToCurrentURL(Exception):
    """Raised by get_object_or_redirect; turned into a 301 by the middleware."""

    def __init__(self, url: str):
        super().__init__(url)
        self.url = url


class SlugRedirectMiddleware:
    """Turns RedirectToCurrentURL into a permanent (301) redirect.

    A 301 tells search engines the page has moved for good, so its ranking
    moves to the new address.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, RedirectToCurrentURL):
            return HttpResponsePermanentRedirect(exception.url)
        return None
