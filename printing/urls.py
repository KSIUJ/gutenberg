from django.urls import path

from printing.views import PrintView

urlpatterns = [
    path('', PrintView.as_view(), name='print'),
]
