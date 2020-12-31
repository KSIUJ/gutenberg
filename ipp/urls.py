from django.urls import re_path

from ipp.views import IppView

urlpatterns = [
    re_path(r'(?P<token>[^/]+)/(?P<printer_id>\d+)/(?P<rel_path>.*)', IppView.as_view(), name='ipp_endpoint')
]
