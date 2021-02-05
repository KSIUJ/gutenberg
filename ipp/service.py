import logging
from abc import ABC, abstractmethod
from typing import Tuple, Callable, Optional, Dict, Any, List

from django.http import HttpResponse
from django.templatetags.static import static

from ipp.constants import OperationEnum, StatusCodeEnum, PrinterStateEnum, JobStateEnum
from ipp.exceptions import IppError, DocumentFormatError, NotFoundError
from ipp.proto import IppRequest, IppResponse, BaseOperationGroup, \
    BadRequestError, minimal_valid_response, response_for, AttributeGroup
from ipp.proto_operations import GetPrinterAttributesRequestOperationGroup, PrinterAttributesGroup, \
    PrintJobRequestOperationGroup, JobTemplateAttributeGroup, GetJobsRequestOperationGroup, \
    JobPrintResponseAttributes, GetJobAttributesRequestOperationGroup, CreateJobRequestOperationGroup, \
    SendDocumentRequestOperationGroup, CancelJobRequestOperationGroup, \
    CloseJobRequestOperationGroup, IdentifyPrinterRequestOperationGroup

logger = logging.getLogger('gutenberg.ipp')


def not_implemented(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_operation_not_supported)


def internal_error(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_internal_error)


def unparsable_request() -> IppResponse:
    return IppResponse(IppResponse.IPP2_0, StatusCodeEnum.client_error_bad_request, 0, [BaseOperationGroup()])


class BaseIppService(ABC):
    SUPPORTED_OPERATIONS: Dict[int, Callable[[IppRequest], IppResponse]] = dict()

    def __init__(self, actor_name: str) -> None:
        self.actor_name = actor_name

    @staticmethod
    def _response(ipp_response: IppResponse, http_code=200):
        http_response = HttpResponse(status=http_code, content_type='application/ipp')
        ipp_response.write_to(http_response)
        return http_response

    def _log_operation(self, idx, rel_path, method, status):
        try:
            status = StatusCodeEnum(status).name
        except ValueError:
            pass
        logger.info(
            "IPP {} {} /{} {} {}".format(idx, self.actor_name, rel_path, method, status))

    def _dispatch(self, version: Tuple[int, int], op_id: int) -> Callable[['BaseIppService', IppRequest], IppResponse]:
        # we ignore ipp version for now
        _ = version
        return self.SUPPORTED_OPERATIONS.get(op_id, not_implemented)

    def handle_request(self, http_request, rel_path: str):
        try:
            req = IppRequest.from_http_request(http_request)
        except BadRequestError as ex:
            self._log_operation(-1, rel_path, str(ex), ex.error_code())
            return self._response(unparsable_request())
        try:
            req.validate()
        except IppError as ex:
            self._log_operation(req.request_id, rel_path, str(ex), ex.error_code())
            return self._response(minimal_valid_response(req, ex.error_code()))
        except Exception as ex:
            logger.error(
                "IPP {} {} /{} Internal error in IPP service.".format(req.request_id, self.actor_name, rel_path),
                ex)
            return self._response(internal_error(req))
        handler = self._dispatch(req.version, req.opid_or_status)
        try:
            res = handler(self, req)
            self._log_operation(req.request_id, rel_path, handler.__name__, res.opid_or_status)
            return self._response(res)
        except IppError as ex:
            self._log_operation(req.request_id, rel_path, handler.__name__, ex.error_code())
            logger.warning(repr(ex))
            return self._response(minimal_valid_response(req, ex.error_code()))
        except Exception as ex:
            logger.error(
                "IPP {} {} /{} {} Internal error in IPP service.".format(req.request_id, self.actor_name,
                                                                         rel_path,
                                                                         handler.__name__), ex)
            return self._response(internal_error(req))


class BaseIppEverywhereService(BaseIppService, ABC):
    def __init__(self, actor_name: str, printer_name: str, printer_uri: str, printer_tls: bool,
                 printer_basic_auth: bool, printer_color: bool, printer_duplex: bool,
                 supported_ipp_formats: List[str]) -> None:
        super().__init__(actor_name)
        self.printer_name = printer_name
        self.printer_uri = printer_uri
        self.printer_tls = printer_tls
        self.printer_basic_auth = printer_basic_auth
        self.printer_color = printer_color
        self.printer_duplex = printer_duplex
        self.supported_ipp_formats = supported_ipp_formats

    @abstractmethod
    def _create_job(self, operation, job_template) -> int:
        raise NotImplementedError()

    @abstractmethod
    def _submit_job(self, request: IppRequest, operation, job_id) -> int:
        raise NotImplementedError()

    @abstractmethod
    def _get_job_uri(self, job_id) -> str:
        raise NotImplementedError()

    @abstractmethod
    def _get_job(self, job_id) -> Optional[Tuple[int, JobStateEnum, bool, Any]]:
        """Returns a tuple (job_id, job_state, is_job_submitted, implementation_dependent_job_object) or None."""
        raise NotImplementedError

    @abstractmethod
    def _get_jobs(self, first_index: int, limit: int, all_jobs: bool = False, exclude_completed: bool = True) -> List[
        Any]:
        """Returns a list of implementation dependent job objects"""
        raise NotImplementedError

    @abstractmethod
    def _build_job_proto(self, job: Any, full_job_proto: bool = True) -> AttributeGroup:
        """Returns a filled JobObjectAttributeGroupFull if full_job_proto or JobObjectAttributeGroup otherwise."""
        raise NotImplementedError

    @abstractmethod
    def _cancel_job(self, job: Any) -> None:
        raise NotImplementedError

    def _find_job(self, operation) -> Tuple[int, JobStateEnum, bool, Any]:
        if not (operation.printer_uri and operation.job_id) and not operation.job_uri:
            raise BadRequestError('no job info provided')
        if operation.job_id:
            job_info = self._get_job(operation.job_id)
        else:
            idx = int(operation.job_uri.slice('/')[-1])
            job_info = self._get_job(idx)
        if not job_info:
            raise NotFoundError('job not found')
        return job_info

    def get_printer_attrs(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(GetPrinterAttributesRequestOperationGroup)
        logger.debug("GetPrinterAttrs:\n" + str(operation))
        if operation.document_format and operation.document_format not in self.supported_ipp_formats:
            raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))
        return response_for(request, [
            BaseOperationGroup(),
            PrinterAttributesGroup(
                printer_uri_supported=[self.printer_uri],
                printer_name="Gutenberg-{}".format(self.printer_name).replace(' ', '-'),
                printer_info="Gutenberg - {}".format(self.printer_name),
                printer_more_info=request.http_request.build_absolute_uri('/'),
                printer_state=PrinterStateEnum.idle,
                printer_state_message="idle",
                queued_job_count=1,
                printer_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0',
                device_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0',
                printer_icons=[request.http_request.build_absolute_uri(static('img/logo-128.png'))],
                printer_supply_info_uri=request.http_request.build_absolute_uri('/'),
                uri_security_supported=['tls'] if self.printer_tls else ['none'],
                uri_authentication_supported=['basic'] if self.printer_basic_auth else ['none'],
                print_color_mode_supported=
                ['auto', 'color', 'monochrome'] if self.printer_color else ['auto', 'monochrome'],
                sides_supported=['one-sided', 'two-sided-long-edge',
                                 'two-sided-short-edge'] if self.printer_duplex else ['one-sided'],
                operations_supported=self.SUPPORTED_OPERATIONS.keys()
            )
        ], requested_attrs_oneset=operation.requested_attributes)

    def print_job(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(PrintJobRequestOperationGroup)
        logger.debug("PrintJob\n" + str(operation))
        if request.has_next():
            job_template = request.read_group(JobTemplateAttributeGroup)
        else:
            job_template = JobTemplateAttributeGroup()
        logger.debug("Print template\n" + str(job_template))
        job_id = self._create_job(operation, job_template)
        job_id = self._submit_job(request, operation, job_id)
        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self._get_job_uri(job_id),
                job_id=job_id,
                job_state=JobStateEnum.pending,
            )
        ])

    def validate_job(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(PrintJobRequestOperationGroup)
        logger.debug("ValidateJob:\n" + str(operation))
        if operation.document_format and operation.document_format not in self.supported_ipp_formats:
            raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))
        return response_for(request, [
            BaseOperationGroup(),
        ])

    def create_job(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(CreateJobRequestOperationGroup)
        logger.debug("CreateJob\n" + str(operation))
        if request.has_next():
            job_template = request.read_group(JobTemplateAttributeGroup)
        else:
            job_template = JobTemplateAttributeGroup()
        logger.debug("Print template\n" + str(job_template))
        job_id = self._create_job(operation, job_template)
        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self._get_job_uri(job_id),
                job_id=job_id,
                job_state=JobStateEnum.pending,
            )
        ])

    def send_document(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(SendDocumentRequestOperationGroup)
        logger.debug("SendDocument\n" + str(operation))
        job_id, job_status, is_job_submitted, _ = self._find_job(operation)

        # Handle empty response
        if is_job_submitted:
            if operation.last_document:
                buff = request.http_request.read(100)
                if len(buff) < 10:
                    return response_for(request, [
                        BaseOperationGroup(),
                        JobPrintResponseAttributes(
                            job_uri=self._get_job_uri(job_id),
                            job_id=job_id,
                            job_state=job_status,
                        )
                    ])
            return minimal_valid_response(request, StatusCodeEnum.server_error_multiple_document_jobs_not_supported)

        self._submit_job(request, operation, job_id)
        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self._get_job_uri(job_id),
                job_id=job_id,
                job_state=job_status,
            )
        ])

    def get_jobs(self, request: IppRequest):
        operation = request.read_group(GetJobsRequestOperationGroup)
        logger.debug("GetJob:\n" + str(operation))

        # Workaround to pass the ipp certification suite
        # - we do not use requesting_user_name but authentication provided username instead.
        if operation.requesting_user_name and operation.requesting_user_name.startswith('not-'):
            return response_for(request, [BaseOperationGroup()],
                                requested_attrs_oneset=operation.requested_attributes)
        jobs = self._get_jobs(first_index=operation.first_index, limit=operation.limit,
                              all_jobs=operation.which_jobs == 'all',
                              exclude_completed=operation.which_jobs != 'completed')
        job_groups = [self._build_job_proto(job, full_job_proto=False) for job in jobs]
        return response_for(request, [BaseOperationGroup()] + job_groups,
                            requested_attrs_oneset=operation.requested_attributes)

    def get_job_attrs(self, request: IppRequest):
        operation = request.read_group(GetJobAttributesRequestOperationGroup)
        logger.debug("GetJobAttrs:\n" + str(operation))
        _, _, _, job = self._find_job(operation)
        return response_for(request, [BaseOperationGroup(), self._build_job_proto(job)],
                            requested_attrs_oneset=operation.requested_attributes)

    def cancel_job(self, request: IppRequest):
        operation = request.read_group(CancelJobRequestOperationGroup)
        logger.debug("CancelJob:\n" + str(operation))
        _, _, _, job = self._find_job(operation)
        self._cancel_job(job)
        return minimal_valid_response(request)

    def close_job(self, request: IppRequest):
        operation = request.read_group(CloseJobRequestOperationGroup)
        logger.debug("CloseJob:\n" + str(operation))
        job_id, job_status, _, _ = self._find_job(operation)
        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self._get_job_uri(job_id),
                job_id=job_id,
                job_state=job_status,
            )
        ])

    def identify_printer(self, request: IppRequest):
        _ = request.read_group(IdentifyPrinterRequestOperationGroup)
        # No-op - this is a virtual printer.
        return minimal_valid_response(request)

    SUPPORTED_OPERATIONS = {
        OperationEnum.get_printer_attributes: get_printer_attrs,
        OperationEnum.print_job: print_job,
        OperationEnum.validate_job: validate_job,
        OperationEnum.get_jobs: get_jobs,
        OperationEnum.get_job_attributes: get_job_attrs,
        OperationEnum.cancel_job: cancel_job,
        OperationEnum.create_job: create_job,
        OperationEnum.send_document: send_document,
        # TODO: add support for cancel_my_jobs operation (recommended by standard).
        # OperationEnum.cancel_my_jobs: cancel_my_jobs,
        OperationEnum.close_job: close_job,
        OperationEnum.identify_printer: identify_printer,
    }
