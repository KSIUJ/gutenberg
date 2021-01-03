from django.urls import path, re_path

from printing.views import webapp, service_worker

urlpatterns = [
    path('', webapp, name='print'),
    re_path('^job/.*', webapp, name='print'),
    path('service-worker.js', service_worker)
]
