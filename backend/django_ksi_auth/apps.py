import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('django_ksi_auth')


class KsiAuthConfig(AppConfig):
    name = "django_ksi_auth"
    verbose_name = "Django KSI Auth plugin"


    @staticmethod
    def verify_correct_setup():
        """
        This function verifies that the middleware is installed correctly.
        The middleware is required to clear expired sessions.

        This function also checks if KsiAuthMiddleware is placed directly after Django's AuthenticationMiddleware.
        This is recommended to avoid accessing the user object if the session has expired.
        """

        try:
            our_index = settings.MIDDLEWARE.index('django_ksi_auth.middleware.KsiAuthMiddleware')
        except ValueError:
            raise ImproperlyConfigured("KsiAuthMiddleware is not installed! It is required for the refreshing and expiration of sessions")

        try:
            django_auth_index = settings.MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware')
        except ValueError:
            logger.warning("Django AuthenticationMiddleware is not installed! It is required for authentication")
            return # The index check is skipped in this case

        if our_index != django_auth_index + 1:
            logger.warning("KsiAuthMiddleware should be placed directly after Django's AuthenticationMiddleware in the MIDDLEWARE list")


    def ready(self):
        self.verify_correct_setup()
