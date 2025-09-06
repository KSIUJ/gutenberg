import logging
from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse

from django_ksi_auth.client import OidcClient

logger = logging.getLogger('ksi_auth.django')


def get_login_redirect_uri(request: HttpRequest) -> str:
    return request.build_absolute_uri(reverse("ksi_auth_callback"))


def get_logout_redirect_uri(request: HttpRequest) -> str:
    return request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)


oidc_client: Optional[OidcClient] = None


def fetch_oidc_client():
    global oidc_client

    if oidc_client is not None:
        logger.warning("The OidcClient was already fetched with fetch_oidc_client()")
        return

    oidc_client = OidcClient.load(
        client_id = settings.KSI_AUTH_PROVIDER['client_id'],
        client_secret = settings.KSI_AUTH_PROVIDER['client_secret'],
        issuer = settings.KSI_AUTH_PROVIDER['issuer'],
    )
