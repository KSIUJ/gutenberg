import django_cas_ng.views
from django.conf.urls import url
from django.urls import path

from printing.views import PrintView

urlpatterns = [
    url(r'^$', PrintView.as_view(), name='print'),
    path('accounts/login/', django_cas_ng.views.LoginView.as_view(), name='cas_ng_login'),
    path('accounts/logout/', django_cas_ng.views.LogoutView.as_view(), name='cas_ng_logout'),
    path('accounts/callback/', django_cas_ng.views.CallbackView.as_view(), name='cas_ng_proxy_callback'),
]
