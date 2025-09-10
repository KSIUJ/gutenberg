"""
The error views defined in this module return JSON error responses
instead of the default Django HTML error pages if the request has
the `Accept` header set to `application/json`.

NOTE: Django does not call these handlers if the `DEBUG` setting is set to `True`.

See https://docs.djangoproject.com/en/5.2/topics/http/views/#customizing-error-views
"""

from django.http import JsonResponse, HttpRequest
from django.views import defaults

def _json_error_view(_request: HttpRequest, message: str, status_code: int):
    return JsonResponse({
        'kind': 'Other',
        'message': message,
        'detail': None,
    }, status=status_code)

def _return_json(request: HttpRequest):
    """
    Determines whether the request should return JSON or HTML error responses.
    If the request does not list `application/json` in its `Accept` header, it returns `False`.
    If both the `application/json` and `text/html` mime types are listed,
    it returns `True` if the `application/json` mime type is listed first.`
    """

    accept_parts = (part.split(';') for part in request.META.get('HTTP_ACCEPT', '*/*').split(','))
    mime_types = list(part[0].strip() for part in accept_parts if len(part) > 0)

    try:
        json_index = mime_types.index('application/json')
    except ValueError:
        return False

    try:
        html_index = mime_types.index('text/html')
    except ValueError:
        return True

    return json_index < html_index


def bad_request(request: HttpRequest, exception=None):
    if _return_json(request):
        return _json_error_view(request, "Bad request", 400)
    return defaults.bad_request(request, exception)


def permission_denied(request: HttpRequest, exception=None):
    if _return_json(request):
        return _json_error_view(request, "Permission denied", 403)
    return defaults.permission_denied(request, exception)


def page_not_found(request: HttpRequest, exception=None):
    if _return_json(request):
        return _json_error_view(request, "Requested endpoint not found", 404)
    return defaults.page_not_found(request, exception)


def server_error(request: HttpRequest):
    if _return_json(request):
        return _json_error_view(request, "Internal server error", 500)
    return defaults.server_error(request)
