from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'n7+3u12_59wy_kzvecb^w^jrpi(m#(gl8^qe92kvclkd9!=-h)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
