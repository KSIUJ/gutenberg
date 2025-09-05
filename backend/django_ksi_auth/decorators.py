from datetime import timedelta
from functools import wraps

from django.conf import settings

from django_ksi_auth.consts import SKIP_SSO_CHECK_COOKIE
from django_ksi_auth.utils import redirect_to_oidc_login, is_ksi_auth_backend_enabled


def ksi_auth_check_sso(function):
    """
    This view decorator redirects unauthenticated users to the OIDC authentication endpoint with `prompt=none`,
    to check if they have an active SSO session.

    After this check, a cookie is set to prevent it from being performed again.
    The max age of the cookie is configurable via the `KSI_AUTH_SSO_CHECK_COOLDOWN_SECONDS` setting.
    """


    def should_run_check(request):
        if request.user.is_authenticated:
            return False

        if not is_ksi_auth_backend_enabled():
            return False

        if SKIP_SSO_CHECK_COOKIE in request.COOKIES:
            return False

        return True


    @wraps(function)
    def wrap(request, *args, **kwargs):
        if should_run_check(request):
            response = redirect_to_oidc_login(request, request.get_full_path(), prompt_none=True)
            cooldown_seconds = getattr(settings, 'KSI_AUTH_SSO_CHECK_COOLDOWN_SECONDS', 300)
            response.set_cookie(SKIP_SSO_CHECK_COOKIE, max_age=timedelta(seconds=cooldown_seconds))
            return response

        return function(request, *args, **kwargs)

    return wrap


def ksi_auth_login_required(function):
    """
    This view decorator verifies that the user is authenticated and if not,
    redirects directly to the OIDC login page if the `KsiAuthBackend` is enabled
    or to the `LOGIN_URL` otherwise.

    This is similar to the `@login_required` decorator from `django.contrib.auth`,
    but it can redirect directly to the OIDC login page, without redirecting to the `LoginView` first.
    """

    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_oidc_login(request, request.get_full_path())

        return function(request, *args, **kwargs)

    return wrap
