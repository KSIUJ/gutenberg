from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils.crypto import get_random_string
from oic.oic import Client
from oic.oic.message import RegistrationResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

from .consts import STATES_SESSION_KEY

OIDC_SCOPE = "openid email"

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


# @sensitive_variables
def redirect_to_oidc_login(request, next_url: str, prompt_none: bool = False):
    """
    Redirects to the OIDC login page if the `KsiAuthBackend` is enabled or to the `LOGIN_URL` otherwise.
    """

    if next_url is None:
        raise ValueError("next_url must be provided")
    # TODO: Validate next url here or in the calling code (and document this)

    # TODO: Check if the backend is enabled
    ksi_auth_enabled = True
    # If the `KsiAuthBackend` is not enabled, redirect to `LOGIN_URL` instead of redirecting to the OIDC provider.
    #
    # Note: This could result in an infinite loop if the view at `LOGIN_URL` uses `redirect_to_oidc_login`
    #       when the `KsiAuthBackend` is not enabled.
    #       The default `BaseLoginView` calls `redirect_to_oidc_login` only if the `KsiAuthBackend` is enabled,
    #       so this is not a problem when the `LOGIN_URL` is (a subclass of) `KsiAuthBackend`.
    if not ksi_auth_enabled:
        redirect_to_login(next_url)

    client = _get_client(request)

    state = get_random_string(32)
    nonce = get_random_string(32)
    if not STATES_SESSION_KEY in request.session:
        request.session[STATES_SESSION_KEY] = {}
    # TODO: mozilla-django-auth limits the number of stored states, we could do it too
    request.session[STATES_SESSION_KEY][state] = {
        'nonce': nonce,
        'next_url': next_url,
    }
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
