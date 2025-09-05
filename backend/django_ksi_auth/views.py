from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import redirect
from django.views.generic.base import View
from oic.oic.message import AuthorizationResponse, TokenErrorResponse, AccessTokenResponse

from django_ksi_auth.auth_backend import KsiAuthBackend
from django_ksi_auth.consts import SESSION_TOKENS_SESSION_KEY, STATES_SESSION_KEY
from django_ksi_auth.utils import redirect_to_oidc_login, _get_client, OIDC_SCOPE, is_ksi_auth_backend_enabled, \
    is_user_authenticated_with_ksi_auth


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

        if not is_ksi_auth_backend_enabled():
            # type(self) returns `BaseLoginView` or a subclass of it.
            # Calling `fallback_view` in this way avoids passing `self` as an argument to `fallback_view`.
            return type(self).fallback_view(request)

        return redirect_to_oidc_login(request, next_url)


class CallbackView(View):
    # @sensitive_variables
    def get(self, request):
        client = _get_client(request)

        authorization_response = client.parse_response(AuthorizationResponse, info=request.GET, sformat="dict")
        state = authorization_response['state']

        try:
            print(request.session.get(STATES_SESSION_KEY, 'sus'))
            print(request.session.get(STATES_SESSION_KEY, {})[state])
            state_entry = request.session.get(STATES_SESSION_KEY, {})[state]
        except KeyError:
            # This message is intended to be shown to the user, the missing session information is not
            # an indication of an attack by itself.
            raise SuspiciousOperation("Failed to find info necessary to complete authentication in the session")

        request_args = {
            "code": authorization_response["code"],
        }

        # TODO: PKCE?

        response = client.do_access_token_request(scope=OIDC_SCOPE, state=state, request_args=request_args)
        if isinstance(response, TokenErrorResponse):
            print(response)
            # TODO: Replace this exception
            raise Exception("Failed to get access token")
        if not isinstance(response, AccessTokenResponse):
            # TODO: Replace this exception
            raise Exception("Unexpected token response type")

        if state_entry['nonce'] != response["id_token"]["nonce"]:
            raise SuspiciousOperation("The authentication request has been tampered with, cannot continue")

        KsiAuthBackend.login(request, response)
        if STATES_SESSION_KEY in request.session:
            del request.session[STATES_SESSION_KEY][state]
            # Modifying an inner dict does not trigger the session save automatically,
            # setting `request.session.modified` makes sure that the session is saved.
            # See https://docs.djangoproject.com/en/5.2/topics/http/sessions/#when-sessions-are-saved
            request.session.modified = True

        return redirect(state_entry['next_url'])

class LogoutView(View):
    # Only POST is allowed and CSRF protection is not disabled to avoid CSRF redirects
    # from signing the user out from this app and the OIDC identity provider.
    def post(self, request):
        try:
            id_token_hint = request.session[SESSION_TOKENS_SESSION_KEY]["id_token"]
        except KeyError:
            id_token_hint = None
        django_ksi_auth_used = is_user_authenticated_with_ksi_auth(request)

        # `logout` also clears the session, so the session is read before calling `logout`.
        logout(request)

        # Skip the OIDC logout if the user didn't use the KSI auth backend to sign in
        if not django_ksi_auth_used:
            return redirect(settings.LOGOUT_REDIRECT_URL)

        client = _get_client(request)

        # TODO: Return to the LOGOUT_REDIRECT_URL after logout. Document this.
        request_args = {
            "id_token_hint": id_token_hint,
        }
        logout_req = client.construct_EndSessionRequest(request_args=request_args)
        logout_url = logout_req.request(client.end_session_endpoint)

        return redirect(logout_url)
