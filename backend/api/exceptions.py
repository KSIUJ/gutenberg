from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    #TODO add more comments
    response = exception_handler(exc, context)

    if response is not None:
        if not isinstance(exc, ValidationError): #standard error format
            response.data = {
                'kind': type(exc).__name__, #type of error
                'message': response.data['detail'],
                'detail': None
            }
            if isinstance(response.data['message'], list):
                response.data['message'] = response.data['message'][0]
                response.data['detail'] = response.data['message'][1:]
        else: #validation error format
            response.data = {
                'kind': type(exc).__name__,
                'errors': response.data
            }
    return response
