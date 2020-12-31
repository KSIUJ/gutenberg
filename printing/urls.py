from django.urls import path, re_path

from printing.views import PrintView, ipp_info

urlpatterns = [
    path('', PrintView.as_view(), name='print'),
    re_path(r'ippinfo/(?P<printer_id>\d+)/', ipp_info, name='ipp_info')
]
