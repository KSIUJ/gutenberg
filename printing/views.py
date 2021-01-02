from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.views import serve


@login_required
def webapp(request):
    return serve(request, "index.html")
