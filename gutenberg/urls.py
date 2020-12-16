"""gutenberg URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import django_cas_ng.views
from django.conf.urls import include
from django.contrib import admin
from django.urls import path

import ipp.urls
import printing.urls

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include(printing.urls)),
    path('ipp/', include(ipp.urls)),

    path('accounts/login/', django_cas_ng.views.LoginView.as_view(),
         name='cas_ng_login'),
    path('accounts/logout/', django_cas_ng.views.LogoutView.as_view(),
         name='cas_ng_logout'),
    path('accounts/callback/', django_cas_ng.views.CallbackView.as_view(),
         name='cas_ng_proxy_callback'),
]
