from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.views import serve


@login_required
def webapp(request):
    return serve(request, "index.html")


def service_worker(request):
    return serve(request, "service-worker.js")
