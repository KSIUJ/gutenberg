import logging

from django.conf import settings
from django.contrib.auth import get_backends, BACKEND_SESSION_KEY, logout
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils.crypto import get_random_string
from django.utils.module_loading import import_string
from oic.oic import Client
from oic.oic.message import RegistrationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

from .auth_backend import KsiAuthBackend
from .consts import STATES_SESSION_KEY

OIDC_SCOPE = "openid email"

logger = logging.getLogger('django_ksi_auth')

# TODO: Right now every time a call to this function is made,
#       the client info is requested from the OIDC provider.
# @sensitive_variables
def _get_client(request):
    # Based on
    # https://github.com/CZ-NIC/pyoidc/blob/a4cff6dbee32f246c8ffd3375091e53ab212f3a2/oidc_example/rp2/oidc.py#L87-L109
    # and https://pyoidc.readthedocs.io/en/latest/examples/rp.html

    client = Client(
        client_authn_method=CLIENT_AUTHN_METHOD,
    )
    client.redirect_uris = [
        request.build_absolute_uri(reverse("ksi_auth_callback")),
    ]
    client.provider_config(settings.KSI_AUTH_PROVIDER['issuer'])
    client.store_registration_info(RegistrationResponse(
        client_id=settings.KSI_AUTH_PROVIDER['client_id'],
        client_secret=settings.KSI_AUTH_PROVIDER['client_secret'],
    ))
    return client


def is_ksi_auth_backend_enabled():
    # The list returned from `get_backends()` contains INSTANCES of the backends.
    return any(isinstance(backend, KsiAuthBackend) for backend in get_backends())


def is_user_authenticated_with_ksi_auth(request):
    # This function is based on mozilla-django-oidc:
    # https://github.com/mozilla/mozilla-django-oidc/blob/774b140b9311c6c874c199bfdb266e51f36740a7/mozilla_django_oidc/middleware.py#L104C9-L109C82

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

    client = _get_client(request)

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

    request_args = {
        'client_id': settings.KSI_AUTH_PROVIDER['client_id'],
        'response_type': "code",
        'scope': OIDC_SCOPE,
        'nonce': nonce,
        "redirect_uri": client.redirect_uris[0],
        "state": state,
    }
    if prompt_none:
        request_args['prompt'] = 'none'

    auth_req = client.construct_AuthorizationRequest(request_args=request_args)
    login_url = auth_req.request(client.authorization_endpoint)

    return redirect(login_url)
