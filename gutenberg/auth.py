from secrets import token_urlsafe
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import transaction
from django.utils.http import is_safe_url
from mozilla_django_oidc import auth


class OIDCAuthenticationBackend(auth.OIDCAuthenticationBackend):

    def get_username(self, claims):
        return claims.get('email')

    def filter_users_by_claims(self, claims):
        sub = claims.get('email')
        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username=sub)

    def create_or_update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.email = claims.get('email')
        user.is_staff = user.is_superuser = settings.OIDC_ADMIN_ROLE in claims.get('roles')
        if not user.api_key:
            user.api_key = token_urlsafe(64)
        user.save()
        self.update_groups(user, claims)
        return user

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        return self.create_or_update_user(user, claims)

    def update_user(self, user, claims):
        return self.create_or_update_user(user, claims)

    def update_groups(self, user, claims):
        """
        Transform roles obtained from keycloak into Django Groups and
        add them to the user. Note that any role not passed via keycloak
        will be removed from the user.
        """
        with transaction.atomic():
            user.groups.clear()
            for role in claims.get('roles'):
                group, _ = Group.objects.get_or_create(name=role)
                group.user_set.add(user)

    def get_userinfo(self, access_token, id_token, payload):
        """
        Get user details from the access_token and id_token and return
        them in a dict.
        """
        userinfo = super().get_userinfo(access_token, id_token, payload)
        accessinfo = self.verify_token(access_token, nonce=payload.get('nonce'))
        roles = accessinfo.get('realm_access', {}).get('roles', [])

        userinfo['roles'] = roles
        return userinfo


def get_next_url_post(request, redirect_field_name):
    next_url = request.POST.get(redirect_field_name)
    if next_url:
        kwargs = {
            'url': next_url,
            'require_https': getattr(settings,
                                     'OIDC_REDIRECT_REQUIRE_HTTPS', request.is_secure())
        }

        hosts = list(getattr(settings, 'OIDC_REDIRECT_ALLOWED_HOSTS', []))
        hosts.append(request.get_host())
        kwargs['allowed_hosts'] = hosts

        is_safe = is_safe_url(**kwargs)
        if is_safe:
            return next_url
    return None


def oidc_op_logout(request):
    oidc_op_logout_endpoint = settings.OIDC_OP_LOGOUT_ENDPOINT
    redirect_field_name = getattr(settings, 'OIDC_REDIRECT_FIELD_NAME', 'next')
    redirect_url = get_next_url_post(request, redirect_field_name)
    if redirect_url is None:
        redirect_url = getattr(settings, 'LOGOUT_REDIRECT_URL', '/')
    redirect_url = request.build_absolute_uri(redirect_url)
    return '{}?redirect_uri={}'.format(oidc_op_logout_endpoint, quote(redirect_url, safe=''))
