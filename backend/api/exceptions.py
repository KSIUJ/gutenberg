from rest_framework.exceptions import ValidationError, APIException, \
    NotAuthenticated, PermissionDenied, AuthenticationFailed
    
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    #TODO add more comments
    
    def kind_type(exc): #TODO explain
        if isinstance(exc, ValidationError):
            return 'ValidationError'
        elif isinstance(exc, NotAuthenticated):
            return 'NotAuthenticated'
        elif isinstance(exc, AuthenticationFailed):
            return 'AuthenticationFailed'
        elif isinstance(exc, PermissionDenied):
            return 'PermissionDenied'
        else:
            return "Other"
    
    response = Response()
    response.status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', None)
    additional_info = getattr(exc, 'additional_info', None)
    if not isinstance(exc, ValidationError): #standard error format
        response.data = {
            'kind': kind_type(exc),
            'message': detail,
            'detail': additional_info
        }
    else: #validation error format
        response.data = {
            'kind': kind_type(exc),
            'errors': detail
        }
    return response

class UnsupportedDocument(APIException):
    status_code = 400
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