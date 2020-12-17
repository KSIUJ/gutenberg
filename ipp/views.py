from django.http import HttpResponse, HttpRequest

# Create your views here.
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from common.models import User
from ipp.service import IppService


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
        user = User.objects.filter(api_key=token).first()
        if not user:
            return HttpResponse(status=403, content_type='plain/text')
        service = IppService(user)
        return service.handle_request(request, rel_path)
