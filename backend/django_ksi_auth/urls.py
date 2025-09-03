from django.urls.conf import path

from django_ksi_auth.views import LoginView, CallbackView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('callback/', CallbackView.as_view(), name='ksi_auth_callback'),
]
