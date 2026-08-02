from django.apps import AppConfig


class ControlConfig(AppConfig):
    name = 'control'

    def ready(self):
        try:
            import control.signals  # noqa: F401
        except ModuleNotFoundError:
            pass
