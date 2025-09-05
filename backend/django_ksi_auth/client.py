import logging
from typing import Type, TypeVar, Optional

import requests
from django.conf import settings
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.http import HttpRequest
from django.urls import reverse
from oic.oauth2.message import SchemeError
from oic.oic import EndSessionRequest
from oic.oic.message import Message, ProviderConfigurationResponse, AuthorizationRequest, AuthorizationResponse, \
    AccessTokenResponse, AccessTokenRequest
from oic.utils.keyio import KeyJar

logger = logging.getLogger('django_ksi_auth')
TMessage = TypeVar('TMessage', bound=Message)


# TODO: Try to remove any Django dependencies from this file,
#       to make it usable with FastAPI
class OidcClient:
    OIDC_SCOPE = "openid email"


    def __init__(self):
        self.provider_configuration = None
        self.keyjar = None
        self.client_id = settings.KSI_AUTH_PROVIDER['client_id']
        self.client_secret = settings.KSI_AUTH_PROVIDER['client_secret']


    def _handle_response(
        self,
        response: requests.Response,
        response_type: Type[TMessage],
        ignore_scheme_error: bool = False,
    ) -> TMessage:
        print(response.json())
        response.raise_for_status()
        message = response_type()
        message.from_dict(response.json())

        if ignore_scheme_error:
            try :
                message.verify(keyjar=self.keyjar)
            except SchemeError:
                logger.error("Got SchemeError when verifying response from OIDC Provider", exc_info=True)
                pass
        else:
            message.verify(keyjar=self.keyjar)

        return message


    def _get_request(self, response_type: Type[TMessage], url, ignore_scheme_error: bool = False) -> TMessage:
        response = requests.get(url)
        return OidcClient._handle_response(self, response, response_type, ignore_scheme_error)


    def _authenticated_post_request(self, response_type: Type[TMessage], url: str, request_body: Message) -> TMessage:
        response = requests.post(url, data=request_body.to_dict(), auth=(self.client_id, self.client_secret))
        return self._handle_response(response, response_type)


    def _create_redirect_url(self, base_url: str, message: TMessage) -> str:
        message.verify(keyjar=self.keyjar)
        return base_url + "?" + message.to_urlencoded()


    def _load_jwks_keys(self):
        self.keyjar = KeyJar()
        self.keyjar.add(self.provider_configuration["issuer"], self.provider_configuration['jwks_uri'])


    def load(self):
        config_url = settings.KSI_AUTH_PROVIDER['issuer']
        if not config_url.endswith("/"):
            config_url += "/"
        config_url += ".well-known/openid-configuration"

        # TODO: ignore_scheme_error
        configuration = self._get_request(ProviderConfigurationResponse, config_url, ignore_scheme_error=True)
        if configuration.get("issuer") != settings.KSI_AUTH_PROVIDER['issuer']:
            raise ImproperlyConfigured("The issuer returned by the OIDC Provider does not match the one configured")
        self.provider_configuration = configuration
        self._load_jwks_keys()


    @staticmethod
    def get_redirect_uri(request: HttpRequest) -> str:
        return request.build_absolute_uri(reverse("ksi_auth_callback"))


    def get_authentication_url(self, request: HttpRequest, nonce: str, state: str, prompt_none: bool):
        request_args = {
            'client_id': self.client_id,
            'response_type': "code",
            'scope': self.OIDC_SCOPE,
            'nonce': nonce,
            "redirect_uri": self.get_redirect_uri(request),
            "state": state,
        }
        if prompt_none:
            request_args['prompt'] = 'none'

        return self._create_redirect_url(
            self.provider_configuration['authorization_endpoint'],
            AuthorizationRequest(**request_args),
        )


    def get_logout_url(self, request: HttpRequest, id_token_hint: Optional[str]):
        request_args = {
            "id_token_hint": id_token_hint,
            # TODO: Document the need to set logout LOGOUT_REDIRECT_URL to a value specified in
            #       the OIDC provider's configuration.
            "post_logout_redirect_uri": request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL),
        }
        return self._create_redirect_url(
            self.provider_configuration['end_session_endpoint'],
            EndSessionRequest(**request_args),
        )


    def parse_authorization_response(self, request: HttpRequest) -> AuthorizationResponse:
        response = AuthorizationResponse()
        response.from_dict(request.GET)
        response.verify(keyjar=self.keyjar)
        return response


    def exchange_code_for_access_token(self, request: HttpRequest, code: str, expected_nonce: str) -> AccessTokenResponse:
        # TODO: Add PKCE verification

        request_args = {
            'grant_type': 'authorization_code',
            'code': code,
            # The OIDC Provider verifies that this `redirect_uri` is the same as the one provided
            # in the `AuthorizationRequest`.
            # It will not be used for any new redirect.
            'redirect_uri': self.get_redirect_uri(request),
        }
        response = self._authenticated_post_request(
            AccessTokenResponse,
            self.provider_configuration['token_endpoint'],
            AccessTokenRequest(**request_args),
        )

        if expected_nonce != response["id_token"]["nonce"]:
            raise SuspiciousOperation("The authentication request has been tampered with, cannot continue")

        return response


def get_oidc_client() -> OidcClient:
    client = OidcClient()
    # FIXME: Right now every time a call to this function is made,
    #        the client info is requested from the OIDC provider.
    client.load()
    return client
