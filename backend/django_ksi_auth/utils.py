import logging
from datetime import datetime, timedelta, UTC

from django.contrib.auth import get_backends, BACKEND_SESSION_KEY, logout, authenticate, login
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string
from oic.oic.message import AccessTokenResponse

from .auth_backend import KsiAuthBackend
from .client import get_oidc_client, OidcProviderError
from .consts import STATES_SESSION_KEY, SESSION_TOKENS_SESSION_KEY

logger = logging.getLogger('django_ksi_auth')


def is_ksi_auth_backend_enabled():
    # The list returned from `get_backends()` contains INSTANCES of the backends.
    return any(isinstance(backend, KsiAuthBackend) for backend in get_backends())


def is_user_authenticated_with_ksi_auth(request):
    # This function is based on mozilla-django-oidc:
    # https://github.com/mozilla/mozilla-django-oidc/blob/774b140b9311c6c874c199bfdb266e51f36740a7/mozilla_django_oidc/middleware.py#L104C9-L109C82

    if not request.user.is_authenticated:
        return False

    try:
        backend_session = request.session[BACKEND_SESSION_KEY]
    except KeyError:
        return False

    try:
        auth_backend = import_string(backend_session)
    except ImportError:
        logger.warning("Failed to import auth backend specified in the session at BACKEND_SESSION_KEY. Signing the user out", exc_info=True)
        logout(request)
        return False

    # The imported auth_backend is a CLASS TYPE, not an INSTANCE of it.
    return issubclass(auth_backend, KsiAuthBackend)


# @sensitive_variables
def redirect_to_oidc_login(request, next_url: str, prompt_none: bool = False):
    """
    Redirects to the OIDC login page if the `KsiAuthBackend` is enabled or to the `LOGIN_URL` otherwise.
    """

    if next_url is None:
        raise ValueError("next_url must be provided")
    # TODO: Validate next url here or in the calling code (and document this)

    # If the `KsiAuthBackend` is not enabled, redirect to `LOGIN_URL` instead of redirecting to the OIDC provider.
    #
    # Note: This could result in an infinite loop if the view at `LOGIN_URL` uses `redirect_to_oidc_login`
    #       when the `KsiAuthBackend` is not enabled.
    #       The default `BaseLoginView` calls `redirect_to_oidc_login` only if the `KsiAuthBackend` is enabled,
    #       so this is not a problem when the `LOGIN_URL` is (a subclass of) `KsiAuthBackend`.
    if not is_ksi_auth_backend_enabled():
        redirect_to_login(next_url)

    state = get_random_string(32)
    nonce = get_random_string(32)

    states = request.session.get(STATES_SESSION_KEY, {})
    # TODO: mozilla-django-oidc limits the number of stored states, we could do it too
    states[state] = {
        'nonce': nonce,
        'next_url': next_url,
    }
    request.session[STATES_SESSION_KEY] = states
    # Previously, the session was not saved when modifying nested dicts in the session object.
    # This should no longer be a problem, because now the key STATES_SESSION_KEY always gets reassigned,
    # but explicitly marking the session as modified doesn't hurt:
    # See https://docs.djangoproject.com/en/5.2/topics/http/sessions/#when-sessions-are-saved
    request.session.modified = True

    authentication_url = get_oidc_client().get_authentication_url(request, nonce, state, prompt_none)
    return redirect(authentication_url)


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


def _update_session(request, response: AccessTokenResponse, tokens_expiry: TokensExpiry):
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


def ksi_auth_login(request, response: AccessTokenResponse):
    # This constructor is throwing, the initialization should happen before calling `login`
    # to avoid failing to update the session after signing in
    tokens_expiry = TokensExpiry(response)

    # Note that in the response from Keycloak response["id_token"] is a JSON object,
    # but response["access_token"] is a JWT.
    user = authenticate(request, oidc_id_token_claims = response["id_token"], oidc_access_token = response["access_token"])
    if user is None:
        raise ImproperlyConfigured("Failed to authenticate user. Is the KsiAuthBackend enabled?")

    login(request, user)
    _update_session(request, response, tokens_expiry)


def _refresh_access_token(request, refresh_token: str):
    client = get_oidc_client()
    access_token_response = client.refresh_access_token(refresh_token)
    _update_session(request, access_token_response, TokensExpiry(access_token_response))
    # TODO: Update user's groups


def refresh_ksi_auth_session(request):
    if not is_user_authenticated_with_ksi_auth(request):
        return

    try:
        session_tokens = request.session[SESSION_TOKENS_SESSION_KEY]
    except KeyError:
        logger.error("Failed to access SESSION_TOKENS_SESSION_KEY for a user. Signing the user out.")
        logout(request)
        return

    if datetime.fromisoformat(session_tokens["access_expires_at"]) > datetime.now(UTC):
        # The access token is still valid
        return

    logger.debug("The access token has expired, refreshing")
    try:
        _refresh_access_token(request, session_tokens["refresh_token"])
        logger.debug("Refreshed access token")
    except Exception as error:
        if isinstance(error, OidcProviderError) and error.response["error"] == "invalid_grant":
            # This is an expected case, there is no need to raise an error here
            logger.debug("Refresh token has expired, signing the user out")
            logout(request)
            return

        # If anything went wrong, the user should be signed out,
        # since they no longer have a valid access token.
        logger.error("Failed to refresh access token, signing the user out", exc_info=True)
        logout(request)
        raise
