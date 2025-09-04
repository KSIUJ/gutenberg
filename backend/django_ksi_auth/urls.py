from django.urls.conf import path

from django_ksi_auth.views import CallbackView, LogoutView

urlpatterns = [
    path('callback/', CallbackView.as_view(), name='ksi_auth_callback'),
    path('logout/', LogoutView.as_view(), name='ksi_auth_logout'),
]
