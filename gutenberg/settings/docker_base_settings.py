from .base import *

STATIC_ROOT = '/app/staticroot'

STATICFILES_DIRS = [
    '/app/webapp_dist',
]

# Logging
LOGGING['handlers']['print_file']['filename'] = '/var/log/gutenberg/print.log'
LOGGING['handlers']['django_file']['filename'] = '/var/log/gutenberg/django.log'

# Celery
CELERY_BROKER_URL = 'redis://redis:6379'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')