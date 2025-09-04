import logging

from django.contrib.auth import get_backends
from django.core.exceptions import MiddlewareNotUsed

from django_ksi_auth.apps import KsiAuthConfig
from django_ksi_auth.auth_backend import KsiAuthBackend

logger = logging.getLogger('django_ksi_auth')

class KsiAuthMiddleware:
    def __init__(self, get_response):
        # The app also calls this function, but only if it's in the INSTALLED_APPS list
        KsiAuthConfig.verify_correct_setup()

        if not any(isinstance(backend, KsiAuthBackend) for backend in get_backends()):
            logger.info("KsiAuthBackend is not enabled, KsiAuthMiddleware will not be used")
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        # TODO: If the signed in user is using the the KSI auth provider:
        #       - refresh the access token if it has expired
        #           - also update the user's groups here
        #       - if the refresh token has expired too, logout the user and clear the session (calling logout does this)
        #       - handle back channel redirection if necessary

        return self.get_response(request)
