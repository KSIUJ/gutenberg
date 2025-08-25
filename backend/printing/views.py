from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.views import serve
from django.conf import settings
from django.http import HttpResponse


def serve_static_file(request, file="index.html"):
    if settings.NGINX_ACCEL_ENABLED:
        response = HttpResponse(status=204)
        response['X-Accel-Redirect'] = '/static/'+file
        return response
    else:
        return serve(request, file, insecure=True)


@login_required
def webapp(request):
    return serve_static_file(request)


def login(request):
    return serve_static_file(request)


def service_worker(request):
    return serve_static_file(request, "service-worker.js")
