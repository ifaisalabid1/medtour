from django.contrib import admin
from django_tasks_db.admin import DBTaskResultAdmin as BaseDBTaskResultAdmin
from django_tasks_db.models import DBTaskResult
from unfold.admin import ModelAdmin

# django-tasks-db registers a plain admin for task results. Re-register it
# with Unfold's styling so failed emails are easy to spot.
admin.site.unregister(DBTaskResult)


@admin.register(DBTaskResult)
class DBTaskResultAdmin(BaseDBTaskResultAdmin, ModelAdmin):
    pass
