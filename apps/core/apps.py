from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        from .files import connect_file_cleanup
        from .redirects import connect_slug_tracking

        connect_file_cleanup()
        connect_slug_tracking()
