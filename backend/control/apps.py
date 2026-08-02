from django.apps import AppConfig


class ControlConfig(AppConfig):
    name = 'control'

    def ready(self):
        from control import signals  # noqa: F401
