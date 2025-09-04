from django_ksi_auth.views import BaseLoginView
from printing.views import webapp_login


class GutenbergLoginView(BaseLoginView):
    fallback_view = webapp_login
