from django.urls import path, re_path

from printing.views import webapp, login

urlpatterns = [
    path('', webapp, name='print'),
    path('login/', login, name='print'),
    re_path('^jobs/.*', webapp, name='print'),
]
