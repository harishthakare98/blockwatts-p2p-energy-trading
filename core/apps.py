"""
App configuration for core application
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'BlockWatts Core'

    def ready(self):
        """
        Import signals when Django starts
        This ensures that signal handlers are connected
        """
        try:
            import core.signals
        except ImportError:
            pass
