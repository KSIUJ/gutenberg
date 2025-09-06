from django.core.exceptions import MiddlewareNotUsed

from ._common import logger
from .apps import KsiAuthConfig
from .utils import is_ksi_auth_backend_enabled, refresh_ksi_auth_session


class KsiAuthMiddleware:
    def __init__(self, get_response):
        # The app also calls this function, but only if it's in the INSTALLED_APPS list
        KsiAuthConfig.verify_correct_setup()

        if not is_ksi_auth_backend_enabled():
            logger.info("KsiAuthBackend is not enabled, KsiAuthMiddleware will not be used")
            raise MiddlewareNotUsed

        self.get_response = get_response

    def __call__(self, request):
        refresh_ksi_auth_session(request)

        return self.get_response(request)
