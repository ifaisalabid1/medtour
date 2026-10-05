"""Delete stored files that no record points to any more.

Django never deletes files itself: replacing a hospital's photo, or deleting
an enquiry after a data-erasure request, would otherwise leave the old file
in storage forever. For medical documents that's a privacy problem, not just
wasted space.
"""

import logging
from functools import partial

from django.apps import apps
from django.db import models, transaction
from django.db.models.signals import post_delete, pre_save

logger = logging.getLogger(__name__)


def connect_file_cleanup() -> None:
    """Attach the clean-up to every model that has a file or image field."""
    for model in apps.get_models():
        if _file_field_names(model):
            pre_save.connect(
                _delete_replaced_files,
                sender=model,
                dispatch_uid=f"cleanup-replaced-{model._meta.label}",
            )
            post_delete.connect(
                _delete_files_of_deleted_record,
                sender=model,
                dispatch_uid=f"cleanup-deleted-{model._meta.label}",
            )


def _file_field_names(model) -> list[str]:
    return [
        field.name
        for field in model._meta.concrete_fields
        if isinstance(field, models.FileField)
    ]


def _delete_replaced_files(sender, instance, raw=False, **kwargs) -> None:
    if raw or instance._state.adding:
        return
    names = _file_field_names(sender)
    previous = sender._base_manager.filter(pk=instance.pk).only(*names).first()
    if previous is None:
        return
    for name in names:
        old_file = getattr(previous, name)
        if old_file and old_file.name != getattr(instance, name).name:
            _delete_after_commit(old_file)


def _delete_files_of_deleted_record(sender, instance, **kwargs) -> None:
    for name in _file_field_names(sender):
        stored_file = getattr(instance, name)
        if stored_file:
            _delete_after_commit(stored_file)


def _delete_after_commit(stored_file) -> None:
    # Only delete once the database change is final: if the save or delete
    # is rolled back, the record still needs its file.
    transaction.on_commit(
        partial(_delete_quietly, stored_file.storage, stored_file.name)
    )


def _delete_quietly(storage, name: str) -> None:
    # The database change already succeeded; a storage hiccup must not turn
    # it into an error page. Log it so the orphan can be removed by hand.
    try:
        storage.delete(name)
    except Exception:
        logger.exception("Could not delete stored file %s", name)
