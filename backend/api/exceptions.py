from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404 as DjangoHttp404
from rest_framework.exceptions import ValidationError, APIException, \
    NotAuthenticated, PermissionDenied, AuthenticationFailed, NotFound
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """
    This custom Django REST Framework exception handler adds the
    standardized format for error responses.
    The 'kind' field can be used to distinguish "not authenticated" errors
    and "permission denied" errors. It is necessary, because currently
    unauthenticated requests return the 403 Forbidden status code,
    not 401 Unauthorized. See:
    https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication
    Please note that setting the status code to 401 for all "not authenticated" errors
    would, per https://datatracker.ietf.org/doc/html/rfc7235#section-3.1,
    require setting the WWW-Authenticate header.
    """
    # Convert these Django errors to instances of `APIException` before handling them.
    # This is the same behavior as the default DRF exception handler.
    if isinstance(exc, DjangoHttp404):
        exc = NotFound(*exc.args)
    elif isinstance(exc, DjangoPermissionDenied):
        exc = PermissionDenied(*exc.args)

    if not isinstance(exc, APIException):
        # Returns the generic Django 500 response.
        # https://www.django-rest-framework.org/api-guide/exceptions/#generic-error-views
        # https://docs.djangoproject.com/en/5.2/topics/http/views/#customizing-error-views
        return None

    def kind_type(exc):
        if isinstance(exc, ValidationError):
            return 'ValidationError'
        elif isinstance(exc, NotAuthenticated):
            return 'NotAuthenticated'
        elif isinstance(exc, AuthenticationFailed):
            return 'AuthenticationFailed'
        elif isinstance(exc, PermissionDenied):
            return 'PermissionDenied'
        else:
            # More values for `kind` might be added in the future for existing or new error types.
            # Clients should not depend on receiving the `Other` kind to test for a specific error type.
            return "Other"

    response = Response()
    response.status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', "An error occurred.")
    additional_info = getattr(exc, 'additional_info', None)
    if isinstance(exc, ValidationError): #validation error format
        response.data = {
            # `ValidationError` is different from other standard subclasses of `ApiError`,
            # its `detail` field might contain multiple errors - the `ValidationError` kind was added to support it.
            # Error responses with the `kind` of `ValidationError` have the extra `errors` field.
            'kind': kind_type(exc),
            'message': 'The server received an invalid request',
            'detail': additional_info,
            'errors': detail
        }
    else: #standard error format
        response.data = {
            'kind': kind_type(exc),
            'message': detail,
            'detail': additional_info
        }
    return response

class UnsupportedDocument(APIException):
    status_code = 422
    default_detail = 'The provided document is not supported.'
    default_code = 'unsupported_document'

class InvalidStatus(APIException):
    status_code = 422
    default_detail =  'Invalid Job status for this request.'
    default_code = 'invalid_status'
    additional_info = None

    def __init__(self, detail=None, code=None, additional_info=None):
        if additional_info:
            self.additional_info = additional_info

        super().__init__(detail, code)
