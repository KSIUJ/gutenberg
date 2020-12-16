from django.http import HttpResponse, HttpRequest

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ipp.service import IppService

service = IppService()


class IppView(View):
    http_method_names = ['get', 'post', 'options']

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, rel_path: str, *args, **kwargs):
        if rel_path == '':
            return HttpResponse(b'This is gutenberg ipp-server', content_type='text/plain')
        # elif rel_path.endswith('.ppd'):
        #     return HttpResponse(behaviour.ppd, content_type='text/plain')
        else:
            return HttpResponse(b'Page does not exist', status=404, content_type='text/plain')

    def post(self, request: HttpRequest, token, rel_path, *args, **kwargs):
        return service.handle_request(request, token, rel_path)
