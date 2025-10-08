from django.conf import settings
from django.views.static import serve
from django.http import HttpResponse

from ksi_oidc_django.decorators import ksi_oidc_check_sso, ksi_oidc_login_required


def serve_html_file(request, file="200.html"):
    if settings.NGINX_ACCEL_ENABLED:
        response = HttpResponse(status=204)
        response['X-Accel-Redirect'] = '/@webapp-html/'+file
        return response
    else:
        return serve(request, file, settings.GUTENBERG_SPA_HTML_DIR)


@ksi_oidc_check_sso
def webapp_public(request):
    return serve_html_file(request)


@ksi_oidc_login_required
def webapp_require_auth(request):
    return serve_html_file(request)


# This method does not redirect to / or the ?next route if the user is already
# signed in, it is the job of the `OidcLoginView` from the `ksi-oidc-django` package.
def webapp_login(request):
    return serve_html_file(request)
