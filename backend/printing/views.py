from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.views import serve


def webapp_public(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", insecure=True)

@login_required
def webapp_require_auth(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", insecure=True)


def login(request):
    # Serve webpack-built SPA.
    return serve(request, "200.html", insecure=True)
