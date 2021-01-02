from django.urls import path, include
from rest_framework import routers

from api.views import PrintJobViewSet, PrinterViewSet

router = routers.DefaultRouter()
router.register('jobs', PrintJobViewSet)
router.register('printers', PrinterViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
