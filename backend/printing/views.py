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


def login(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", settings.GUTENBERG_SPA_HTML_DIR)
