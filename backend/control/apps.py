from django.apps import AppConfig


class ControlConfig(AppConfig):
    name = 'control'

    def ready(self):
        # Import signal handlers at startup so preview/artefact cleanup is registered.
        import control.signals  # noqa: F401
