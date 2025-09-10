from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404 as DjangoHttp404, JsonResponse
from rest_framework import exceptions


def _get_exception_kind(exc):
    if isinstance(exc, exceptions.ValidationError):
        return 'ValidationError'
    elif isinstance(exc, exceptions.NotAuthenticated):
        return 'NotAuthenticated'
    elif isinstance(exc, exceptions.AuthenticationFailed):
        return 'AuthenticationFailed'
    elif isinstance(exc, exceptions.PermissionDenied):
        return 'PermissionDenied'
    else:
        # More values for `kind` might be added in the future for existing or new error types.
        # Clients should not depend on receiving the `Other` kind to test for a specific error type.
        return "Other"


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
        exc = exceptions.NotFound(*exc.args)
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied(*exc.args)

    if not isinstance(exc, exceptions.APIException):
        # Returns a generic 500 response to avoid leaking internal data unintentionally.
        return JsonResponse(
            {
                'kind': 'Other',
                'message': 'An internal server error occurred.',
                'detail': None,
            },
            status=500,
        )

    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', "An error occurred.")
    additional_info = getattr(exc, 'additional_info', None)

    if isinstance(exc, exceptions.ValidationError): # validation error format
        # `ValidationError` is different from other standard subclasses of `ApiError`,
        # its `detail` field might contain multiple errors - the `ValidationError` kind was added to support it.
        # Error responses with the `kind` of `ValidationError` have the extra `errors` field.
        data = {
            'kind': _get_exception_kind(exc),
            'message': 'The server received an invalid request',
            'detail': additional_info,
            'errors': detail
        }
    else: # standard error format
        data = {
            'kind': _get_exception_kind(exc),
            'message': detail,
            'detail': additional_info
        }

    return JsonResponse(data, status=status_code)


class UnsupportedDocument(exceptions.APIException):
    status_code = 422
    default_detail = 'The provided document is not supported.'
    default_code = 'unsupported_document'


class InvalidStatus(exceptions.APIException):
    status_code = 422
    default_detail =  'Invalid Job status for this request.'
    default_code = 'invalid_status'
    additional_info = None

    def __init__(self, detail=None, code=None, additional_info=None):
        if additional_info:
            self.additional_info = additional_info

        super().__init__(detail, code)
