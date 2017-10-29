from django.conf.urls import url

from printing.views import PrintView

urlpatterns = [
    url(r'^$', PrintView.as_view(), name='print')
]
