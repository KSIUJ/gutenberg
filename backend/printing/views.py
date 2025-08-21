from django.contrib.auth.decorators import login_required
from django.views.static import serve
from django.conf import settings

@login_required
def webapp(request):
    return serve(request, 'index.html', document_root=settings.WHITENOISE_ROOT)

def login(request):
    return serve(request, 'index.html', document_root=settings.WHITENOISE_ROOT)

def service_worker(request):
    return serve(request, 'service-worker.js', document_root=settings.WHITENOISE_ROOT)