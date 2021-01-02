from django.urls import path, re_path

from printing.views import ipp_info, webapp

urlpatterns = [
    path('', webapp, name='print'),
    re_path(r'ippinfo/(?P<printer_id>\d+)/', ipp_info, name='ipp_info'),
]
