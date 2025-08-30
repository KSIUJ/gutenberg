from django.urls import path, re_path

from printing.views import login, webapp_public, webapp_require_auth

urlpatterns = [
    path('', webapp_public, name='print'),
    path('login/', login, name='print'),
    re_path('^print/.*', webapp_require_auth, name='print'),
]
