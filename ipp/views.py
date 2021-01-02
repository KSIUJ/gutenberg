import base64

from django.http import HttpResponse, HttpRequest

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from common.models import User
from control.models import Printer
from ipp.service import IppService


class IppView(View):
    http_method_names = ['get', 'post', 'options']
    BASIC_AUTH_TOKEN = 'basic'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, rel_path: str, *args, **kwargs):
        if rel_path == '':
            return HttpResponse(b'This is gutenberg ipp-server', content_type='text/plain')
        else:
            return HttpResponse(b'Page does not exist', status=404, content_type='text/plain')

    def post(self, request: HttpRequest, printer_id, token, rel_path, *args, **kwargs):
        user = None
        basic_auth = token == self.BASIC_AUTH_TOKEN
        if basic_auth:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            token_type, _, credentials = auth_header.partition(' ')
            if token_type.lower() == 'basic':
                username, password = base64.b64decode(credentials).decode('utf-8', errors='ignore').split(':')
                if password:
                    user = User.objects.filter(username=username, api_key=password).first()
        elif token:
            user = User.objects.filter(api_key=token).first()
        if not user:
            if basic_auth:
                res = HttpResponse(b'Unauthorized', status=401, content_type='text/plain')
                res['WWW-Authenticate'] = 'Basic realm="gutenberg", charset="UTF-8"'
                return res
            else:
                return HttpResponse(b'Forbidden', status=403, content_type='text/plain')
        printer = Printer.objects.filter(id=printer_id).first()
        if not printer:
            return HttpResponse(b'Not found', status=404, content_type='text/plain')
        service = IppService(printer, user, request.is_secure(), basic_auth)
        return service.handle_request(request, rel_path)
