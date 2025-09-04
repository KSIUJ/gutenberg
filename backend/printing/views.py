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


# This method does not redirect to / or the ?next route if the user is already
# signed in, it is the job of the GutenbergLoginView, a subclass of
# BaseLoginView from the docker_ksi_auth package.
def webapp_login(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", settings.GUTENBERG_SPA_HTML_DIR)
