from django.urls import re_path

from ipp.views import IppView

urlpatterns = [
    re_path(r'(?P<rel_path>.*)', IppView.as_view())
]
