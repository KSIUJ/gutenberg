import logging
from datetime import datetime, UTC, timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.http import HttpRequest
from oic.oauth2 import AccessTokenResponse

from django_ksi_auth.client import get_oidc_client
from django_ksi_auth.consts import SESSION_TOKENS_SESSION_KEY

logger = logging.getLogger('django_ksi_auth')


class TokensExpiry:
    def __init__(self, response: AccessTokenResponse):
        refresh_expires_in = response.get("refresh_expires_in", None)
        access_expires_in = response.get("expires_in", None)
        if refresh_expires_in is None:
            raise ValueError("Missing refresh_expires_in in access token response")
        if access_expires_in is None:
            raise ValueError("Missing expires_in in access token response")

        self.refresh_expires_at = datetime.now(UTC) + timedelta(seconds = refresh_expires_in)
        self.access_expires_at = datetime.now(UTC) + timedelta(seconds = access_expires_in)


def sync_roles(user: User, roles: list[str]):
    """
    Transform roles obtained from keycloak into Django Groups and
    add them to the user. Note that any role not passed via Keycloak
    will be removed from the user.
    """

    if settings.KSI_AUTH_PROVIDER['staff_role'] is not None:
        user.is_staff = settings.KSI_AUTH_PROVIDER['staff_role'] in roles
    if settings.KSI_AUTH_PROVIDER['superuser_role'] is not None:
        user.is_superuser = settings.KSI_AUTH_PROVIDER['superuser_role'] in roles
    user.save()

    if settings.KSI_AUTH_PROVIDER['sync_roles_as_groups']:
        with transaction.atomic():
            user.groups.clear()
            for role in roles:
                group, _ = Group.objects.get_or_create(name=role)
                group.user_set.add(user)


def update_session(request: HttpRequest, response: AccessTokenResponse, tokens_expiry: TokensExpiry):
    # TODO: Verify that the id token is for the signed user
    # TODO: Verify sid when back-channel logout is implemented

    # The "refresh_expires_in" is the remaining length of the OIDC client session.
    # When a refresh token is used to get a new access token, a new refresh token is usually granted too,
    # possibly with a different expiration time, so the session expiry should also be updated then.
    request.session.set_expiry(tokens_expiry.refresh_expires_at)

    request.session[SESSION_TOKENS_SESSION_KEY] = {
        "access_token": response["access_token"],
        "access_expires_at": tokens_expiry.access_expires_at.isoformat(),
        "refresh_token": response["refresh_token"],
        "id_token": response["id_token_jwt"],
    }


def refresh_access_token(request: HttpRequest, refresh_token: str):
    client = get_oidc_client()
    access_token_response = client.refresh_access_token(refresh_token)
    update_session(request, access_token_response, TokensExpiry(access_token_response))
    roles = client.get_roles_from_access_token(access_token_response["access_token"])
    sync_roles(request.user, roles)
