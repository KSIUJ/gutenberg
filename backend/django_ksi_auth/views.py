from oic.oic import Client
from oic.oic.message import AuthorizationResponse, RegistrationResponse, TokenErrorResponse, AccessTokenResponse
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic.base import View
from django.utils.crypto import get_random_string
from django.conf import settings

from django_ksi_auth.consts import STATE_SESSION_KEY, NONCE_SESSION_KEY

OIDC_SCOPE = "openid email"

# TODO: Right now every time a call to this function is made,
#       the client info is requested from the OIDC provider.
def _get_client(request):
    # Based on
    # https://github.com/CZ-NIC/pyoidc/blob/a4cff6dbee32f246c8ffd3375091e53ab212f3a2/oidc_example/rp2/oidc.py#L87-L109
    # and
    # https://pyoidc.readthedocs.io/en/latest/examples/rp.html

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


def authenticate_redirect(request):
    client = _get_client(request)

    state = get_random_string(32)
    nonce = get_random_string(32)
    request.session[STATE_SESSION_KEY] = state
    request.session[NONCE_SESSION_KEY] = nonce
    request_args = {
        'client_id': settings.KSI_AUTH_PROVIDER['client_id'],
        'response_type': "code",
        'scope': OIDC_SCOPE,
        'nonce': nonce,
        # TODO: Maybe change, remove?
        "redirect_uri": client.redirect_uris[0],
        "state": state,
    }

    auth_req = client.construct_AuthorizationRequest(request_args=request_args)
    login_url = auth_req.request(client.authorization_endpoint)

    return redirect(login_url)


class LoginView(View):
    def get(self, request):
        return authenticate_redirect(request)

class CallbackView(View):
    def get(self, request):
        client = _get_client(request)

        authorization_response = client.parse_response(AuthorizationResponse, info=request.GET, sformat="dict")

        if not request.session.has_key(STATE_SESSION_KEY):
            # TODO: Replace this exception
            raise Exception("State not found in session")
        if request.session[STATE_SESSION_KEY] != authorization_response["state"]:
            # TODO: Replace this exception
            raise Exception("State mismatch")

        request_args = {
            "code": authorization_response["code"],
            # TODO: Maybe change, remove?
            "redirect_uri": client.redirect_uris[0],
        }

        response = client.do_access_token_request(scope=OIDC_SCOPE, state=authorization_response["state"], request_args=request_args)
        if isinstance(response, TokenErrorResponse):
            print(response)
            # TODO: Replace this exception
            raise Exception("Failed to get access token")
        if not isinstance(response, AccessTokenResponse):
            # TODO: Replace this exception
            raise Exception("Unexpected token response type")
        return HttpResponse(str(response['id_token']))
