from datetime import datetime, timedelta, UTC

from django.http.response import HttpResponse
from django.views.generic.base import View
from oic.oic.message import AuthorizationResponse, TokenErrorResponse, AccessTokenResponse

from django_ksi_auth.auth_backend import KsiAuthBackend
from django_ksi_auth.consts import STATE_SESSION_KEY
from django_ksi_auth.utils import authenticate_redirect, _get_client, OIDC_SCOPE


class LoginView(View):
    # @sensitive_variables
    def get(self, request):
        return authenticate_redirect(request)


class CallbackView(View):
    # @sensitive_variables
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

        # TODO: Shouldn't nonce be compared here and removed from the session?
        # TODO: PKCE?

        response = client.do_access_token_request(scope=OIDC_SCOPE, state=authorization_response["state"], request_args=request_args)
        if isinstance(response, TokenErrorResponse):
            print(response)
            # TODO: Replace this exception
            raise Exception("Failed to get access token")
        if not isinstance(response, AccessTokenResponse):
            # TODO: Replace this exception
            raise Exception("Unexpected token response type")

        if response["refresh_expires_in"] is None:
            raise Exception("Missing refresh_expires_in in access token response")

        refresh_expires_at = datetime.now(UTC) + timedelta(seconds = response["refresh_expires_in"])
        KsiAuthBackend.login(request, response["access_token"], response["refresh_token"], response["id_token"], refresh_expires_at)

        return HttpResponse(str(response))
