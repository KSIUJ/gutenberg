from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied

def auth_exception_handler(exc, context):
    """
    This custom Django REST Framework exception handler adds the
    X-Reason header for error responses.
    The header can be used to distinguish "not authenticated" errors
    ana "permission denied" errors. It is necessary, because currently
    unauthenticated requests return the 403 Forbidden status code,
    not 401 Unauthorized. See:
    https://www.django-rest-framework.org/api-guide/authentication/#sessionauthentication

    Please note that setting the status code to 401 for all "not authenticated" errors
    would, per https://datatracker.ietf.org/doc/html/rfc7235#section-3.1,
    require setting the WWW-Authenticate header.
    """

    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, NotAuthenticated):
            response.headers['X-Reason'] = 'NotAuthenticated'
        elif isinstance(exc, AuthenticationFailed):
            response.headers['X-Reason'] = 'AuthenticationFailed'
        elif isinstance(exc, PermissionDenied):
            response.headers['X-Reason'] = 'PermissionDenied'
        else:
            # More values for X-Reason might be added in the future,
            # clients should not depend on receiving X-Reason: Other
            response.headers['X-Reason'] = 'Other'

    return response
