from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.static import serve


def webapp_public(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", settings.GUTENBERG_SPA_HTML_DIR)


@login_required
def webapp_require_auth(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", settings.GUTENBERG_SPA_HTML_DIR)

# TODO: Redirect to the ?next route if the user is already logged in
#       See the middleware in /webapp/app/pages/login.vue
def login(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", settings.GUTENBERG_SPA_HTML_DIR)
