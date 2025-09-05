import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import Group
from django.core.exceptions import SuspiciousOperation
from django.db import transaction

from .apps import KsiAuthConfig

logger = logging.getLogger('django_ksi_auth')


class KsiAuthBackend(BaseBackend):
    """
    This backend is loosely based on the one from mozilla-django-oidc.
    """

    def __init__(self):
        # The app also calls this function, but only if it's in the INSTALLED_APPS list
        KsiAuthConfig.verify_correct_setup()

        super().__init__()
        self.user_model = get_user_model()


    def _find_existing_user(self, oidc_id_token_claims):
        """
        Finds and returns an existing user stored in the database for the claims in `oidc_id_token_claims`.

        Raises a `SuspiciousOperation` error if there are multiple users with the same sub or email.
        """
        # The implementation is based on `filter_users_by_claims` in mozilla-django-oidc

        # TODO: Use the user's UUID to try to retrieve them if they have already authenticated with OIDC.
        #       The email field should be updated in this case!
        sub_matching_users = self.user_model.objects.none()
        if len(sub_matching_users) > 1:
            raise SuspiciousOperation("Multiple users with the same sub found in Django database")
        if len(sub_matching_users) == 1:
            return sub_matching_users[0]

        email_matching_users = self.user_model.objects.filter(email__iexact=oidc_id_token_claims.get("email"))
        if len(email_matching_users) > 1:
            raise SuspiciousOperation("Multiple users with the same email found in Django database")
        if len(email_matching_users) == 1:
            return email_matching_users[0]

        return None


    def _create_user(self, id_token_claims):
        """
        Creates and returns a new user object with the username and email from `id_token_claims`.

        This method does not call .save() on the user object.
        The user object created by this function should be passed as an argument to `_update_user`.
        """

        email = id_token_claims.get("email")
        username = id_token_claims.get("preferred_username")
        user = self.user_model.objects.create_user(username, email=email)
        return user


    def _update_user(self, user, id_token_claims, access_token):
        user.first_name = id_token_claims.get('given_name', '')
        user.last_name = id_token_claims.get('family_name', '')
        user.email = id_token_claims.get('email')
        # TODO: Replace with own settings
        # user.is_staff = user.is_superuser = settings.OIDC_ADMIN_ROLE in claims.get('roles')
        # TODO: Store the value of the sub claim as an OIDC id.
        user.save()
        self._update_groups(user, id_token_claims)


    def _update_groups(self, user, access_token):
        """
        Transform roles obtained from keycloak into Django Groups and
        add them to the user. Note that any role not passed via Keycloak
        will be removed from the user.
        """
        # TODO: Parse and verify claims from access_token
        access_token_claims = {}
        try:
            roles = access_token_claims['roles']
        except KeyError:
            logger.warning("roles claim not present in access token")
            roles = []

        # TODO: Maybe only some roles should be synced?
        with transaction.atomic():
            user.groups.clear()
            for role in roles:
                group, _ = Group.objects.get_or_create(name=role)
                group.user_set.add(user)


    def authenticate(self, request, oidc_id_token_claims = None, oidc_access_token = None):
        print("KsiAuthBackend.authenticated called")
        if oidc_id_token_claims is None or oidc_access_token is None:
            return None
        print("KsiAuthBackend.authenticated running")

        user = self._find_existing_user(oidc_id_token_claims)
        if user is None:
            user = self._create_user(oidc_id_token_claims)

        self._update_user(user, oidc_id_token_claims, oidc_access_token)
        return user


    def get_user(self, user_id):
        # TODO: Check if the user is active? Or should it not apply to this backend?
        try:
            return self.user_model.objects.get(pk=user_id)
        except self.user_model.DoesNotExist:
            return None
