from django.apps import AppConfig


class ControlConfig(AppConfig):
    name = 'control'

    def ready(self):
        import control.signals  # noqa: F401
