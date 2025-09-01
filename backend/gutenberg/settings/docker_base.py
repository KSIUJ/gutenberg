from .base import *

STATIC_ROOT = '/app/staticroot'

STATICFILES_DIRS = [
    '/app/webapp_public',
]

# The `webapp/.output/html` directory is not copied to the Django containers
GUTENBERG_SPA_HTML_DIR=None

# This is a custom setting that controls how the index.html file is served for the SPA webapp.
# All webapp routes are handled by the Django server to handle authentication.
# If enabled, Django will instruct Nginx to serve the index.html file using the X-Accel-Redirect header.
# If disabled, django.contrib.staticfiles will be used to serve the file.
# See backend/printing/views.py
NGINX_ACCEL_ENABLED=True

# Logging
LOGGING['handlers']['print_file']['filename'] = '/var/log/gutenberg/print.log'
LOGGING['handlers']['django_file']['filename'] = '/var/log/gutenberg/django.log'

# Printing
# Directory to store the printed files in
MEDIA_ROOT = '/var/lib/gutenberg/media_root/'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
