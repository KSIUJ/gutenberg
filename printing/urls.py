from django.urls import path

from printing.views import webapp

urlpatterns = [
    path('', webapp, name='print'),
]
