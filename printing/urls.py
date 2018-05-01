from django.conf.urls import url

from printing.views import LoginView, LogoutView, PrintView

urlpatterns = [
    url(r'^$', PrintView.as_view(), name='print'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^login/$', LoginView.as_view(), name='login'),
]
