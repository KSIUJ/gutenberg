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
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ksi_oidc_django.views import OidcLoginView

import api.urls
import ipp.urls
import printing.urls
from printing.views import webapp_login

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include(printing.urls)),
    path('ipp/', include(ipp.urls)),
    path('api/', include(api.urls)),

    path('login/', OidcLoginView.as_view(fallback_view=webapp_login), name='login'),
    path('oidc/', include('ksi_oidc_django.urls')),
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'Gutenberg'
