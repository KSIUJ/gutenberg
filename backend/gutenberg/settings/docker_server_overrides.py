# This configuration file is used internally in the Dockerfile targets `run_backend` and `run_celery` to modify
# the settings after applying the user-provided `docker_settings.py`.

try:
    from .docker_settings import *
except ImportError:
    raise ImportError(
        'The "docker_settings.py" file was not found. '
        'Please create it based on "backend/gutenberg/settings/docker_settings.py.example" '
        'and mount it at "/etc/gutenberg/docker_settings.py". '
        'Check Gutenberg\'s documentation for more details.'
    )

# If NGINX_ACCEL_ENABLED is set to True then the Django server is not responsible for serving static files.
# In the Dockerfile target `run_backend` some static files are missing, as they are not needed.
# The app django.contrib.staticfiles is removed to disable false-positive warnings about missing static files.
if NGINX_ACCEL_ENABLED:
    INSTALLED_APPS = INSTALLED_APPS.copy()
    INSTALLED_APPS.remove("django.contrib.staticfiles")
