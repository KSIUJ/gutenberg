from django.urls import path, re_path

from printing.views import webapp

urlpatterns = [
    path('', webapp, name='print'),
    re_path('^job/.*', webapp, name='print'),
]
