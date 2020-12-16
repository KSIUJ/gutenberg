from typing import Tuple, Callable

from django.http import HttpResponse

from control.models import PrintingProperties
from ipp.constants import OperationEnum, StatusCodeEnum, PrinterStateEnum
from ipp.exceptions import IppError, DocumentFormatError
from ipp.proto import IppRequest, IppResponse, BaseOperationGroup, \
    BadRequestError, minimal_valid_response, response_for
from ipp.proto_operations import GetPrinterAttributesRequestOperationGroup, PrinterAttributesGroup, \
    PrintJobRequestOperationGroup, JobTemplateAttributeGroup

SUPPORTED_FORMATS = ['application/pdf']


def get_printer_attrs(request: IppRequest) -> IppResponse:
    operation = request.read_group(GetPrinterAttributesRequestOperationGroup)
    if operation.document_format and operation.document_format not in SUPPORTED_FORMATS:
        raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))

    return response_for(request, [
        BaseOperationGroup(),
        PrinterAttributesGroup(
            printer_uri_supported=["ipp://127.0.0.1/ipp/print"],
            printer_name="Gutenberg",
            printer_more_info="http://127.0.0.1/",
            printer_state=PrinterStateEnum.idle,
            printer_state_message="idle",
            queued_job_count=0,
            printer_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0',
            device_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0')
    ])


def print_job(request: IppRequest) -> IppResponse:
    operation = request.read_group(PrintJobRequestOperationGroup)
    if operation.document_format and operation.document_format not in SUPPORTED_FORMATS:
        raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))
    props = PrintingProperties()
    if request.has_next():
        job_template = request.read_group(JobTemplateAttributeGroup)

    data = request.raw_request().read()

    return response_for(request, [
        BaseOperationGroup(),
    ])


def not_implemented(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_operation_not_supported)


def internal_error(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_internal_error)


def unsupported_version(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_version_not_supported)


def unparsable_request() -> IppResponse:
    return IppResponse(IppResponse.IPP2_0, StatusCodeEnum.client_error_bad_request, 0, [BaseOperationGroup()])


def bad_request(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.client_error_bad_request)


class IppService:
    @staticmethod
    def _dispatch(version: Tuple[int, int], op_id: int) -> Callable[[IppRequest], IppResponse]:
        # we ignore ipp version for now
        _ = version
        commands = {
            OperationEnum.get_printer_attributes: get_printer_attrs,
            OperationEnum.print_job: print_job,
        }
        return commands.get(op_id, not_implemented)

    @staticmethod
    def _response(ipp_response: IppResponse, http_code=200):
        http_response = HttpResponse(status=http_code, content_type='application/ipp')
        ipp_response.write_to(http_response)
        return http_response

    def handle_request(self, http_request):
        try:
            req = IppRequest.from_http_request(http_request)
        except BadRequestError:
            return self._response(unparsable_request())
        try:
            req.validate()
            handler = self._dispatch(req.version, req.opid_or_status)
            res = handler(req)
            return self._response(res)
        except IppError as ex:
            return self._response(minimal_valid_response(req, ex.error_code()))
        except ValueError as ex:
            return self._response(internal_error(req))
        except Exception as ex:
            print(ex)
            raise ex
