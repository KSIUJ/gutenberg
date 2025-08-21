from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.views import serve


@login_required
def webapp(request):
    # Serve webpack-built SPA.
    return serve(request, "index.html", insecure=True)


def login(request):
    # Serve webpack-built SPA.
    return serve(request, "index.html", insecure=True)


def service_worker(request):
    # Serve webpack-built SPA.
    return serve(request, "service-worker.js", insecure=True)
