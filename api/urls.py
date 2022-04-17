from django.urls import path, include
from rest_framework import routers

from api.views import PrintJobViewSet, PrinterViewSet, MeView, ResetApiTokenView, LoginApiView

router = routers.DefaultRouter()
router.register('jobs', PrintJobViewSet)
router.register('printers', PrinterViewSet)

urlpatterns = [
    path('me/', MeView.as_view()),
    path('resettoken/', ResetApiTokenView.as_view()),
    path('login/', LoginApiView.as_view()),
    path('', include(router.urls)),
]
