from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.http import HttpResponse


def serve_html_file(request, file="200.html"):
    if settings.NGINX_ACCEL_ENABLED:
        response = HttpResponse(status=204)
        response['X-Accel-Redirect'] = '/@webapp-html/'+file
        return response
    else:
        return serve(request, file, settings.GUTENBERG_SPA_HTML_DIR)


def webapp_public(request):
    return serve_html_file(request)


@login_required
def webapp_require_auth(request):
    return serve_html_file(request)


# TODO: Redirect to the ?next route if the user is already logged in
#       See the middleware in /webapp/app/pages/login.vue
def login(request):
    return serve_html_file(request)
