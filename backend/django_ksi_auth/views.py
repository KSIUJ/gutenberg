from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.views.generic.base import View
from oic.oic.message import AuthorizationResponse, TokenErrorResponse, AccessTokenResponse

from django_ksi_auth.auth_backend import KsiAuthBackend
from django_ksi_auth.consts import STATE_SESSION_KEY, SESSION_TOKENS_SESSION_KEY
from django_ksi_auth.utils import redirect_to_oidc_login, _get_client, OIDC_SCOPE


# TODO: Add a note in the docs that this view should be set as LOGIN_URL
#       A warning could also be added here if it's not?
# TODO: Document this!
class BaseLoginView(View):
    fallback_view = DjangoLoginView.as_view()

    def get(self, request):
        next_url = request.GET.get("next") or settings.LOGIN_REDIRECT_URL
        if request.user.is_authenticated:
            # TODO: Sanitize the redirect URL
            return redirect(next_url)

        # TODO: Check if the backend is enabled
        ksi_auth_enabled = True
        if not ksi_auth_enabled:
            return self.fallback_view(request)

        return redirect_to_oidc_login(request, next_url)


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

        KsiAuthBackend.login(request, response)

        return HttpResponse(str(response))

class LogoutView(View):
    # Only POST is allowed and CSRF protection is not disabled to avoid CSRF redirects
    # from signing the user out from this app and the OIDC identity provider.
    def post(self, request):
        try:
            id_token_hint = request.session[SESSION_TOKENS_SESSION_KEY]["id_token"]
        except KeyError:
            id_token_hint = None

        # TODO: Check if KsiAuthBackend was used to sign the current user in.
        #       The redirect to the Identity Provider should only happen if it was.

        # `logout` also clears the session
        logout(request)

        client = _get_client(request)

        # TODO: Return to the LOGOUT_REDIRECT_URL after logout. Document this.
        request_args = {
            "id_token_hint": id_token_hint,
        }
        logout_req = client.construct_EndSessionRequest(request_args=request_args)
        logout_url = logout_req.request(client.end_session_endpoint)

        return redirect(logout_url)
