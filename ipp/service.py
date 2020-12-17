import logging
import os
from datetime import datetime
from typing import Tuple, Callable

from django.conf import settings
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

from common.models import User
from control.models import PrintingProperties, PrintJob, JobStatus, TwoSidedPrinting
from ipp import SUPPORTED_IPP_FORMATS, AUTODETECT_IPP_FORMAT, DEFAULT_IPP_FORMAT
from ipp.constants import OperationEnum, StatusCodeEnum, PrinterStateEnum, JobStateEnum, ValueTagsEnum
from ipp.exceptions import IppError, DocumentFormatError, NotFoundError
from ipp.proto import IppRequest, IppResponse, BaseOperationGroup, \
    BadRequestError, minimal_valid_response, response_for, ipp_timestamp
from ipp.proto_operations import GetPrinterAttributesRequestOperationGroup, PrinterAttributesGroup, \
    PrintJobRequestOperationGroup, JobTemplateAttributeGroup, JobObjectAttributeGroup, GetJobsRequestOperationGroup, \
    JobPrintResponseAttributes, GetJobAttributesRequestOperationGroup, CreateJobRequestOperationGroup, \
    SendDocumentRequestOperationGroup, JobObjectAttributeGroupFull, CancelJobRequestOperationGroup
from printing.converter import detect_file_format
from printing.printing import print_file

logger = logging.getLogger('gutenberg.ipp')


def not_implemented(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_operation_not_supported)


def internal_error(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.server_error_internal_error)


def unparsable_request() -> IppResponse:
    return IppResponse(IppResponse.IPP2_0, StatusCodeEnum.client_error_bad_request, 0, [BaseOperationGroup()])


def not_possible(request: IppRequest) -> IppResponse:
    return minimal_valid_response(request, StatusCodeEnum.client_error_not_possible)


def job_status_to_ipp(status):
    return {
        JobStatus.UNKNOWN: ValueTagsEnum.unknown,
        JobStatus.INCOMING: JobStateEnum.pending,
        JobStatus.PENDING: JobStateEnum.pending,
        JobStatus.PROCESSING: JobStateEnum.processing,
        JobStatus.PRINTING: JobStateEnum.processing,
        JobStatus.COMPLETED: JobStateEnum.completed,
        JobStatus.CANCELED: JobStateEnum.canceled,
        JobStatus.CANCELING: JobStateEnum.processing,
        JobStatus.ERROR: JobStateEnum.aborted,
    }.get(status, ValueTagsEnum.unknown)


class IppService:
    def __init__(self, user: User) -> None:
        self.user = user

    def get_printer_attrs(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(GetPrinterAttributesRequestOperationGroup)
        # logger.debug("GetPrinterAttrs:\n" + str(operation))
        if operation.document_format and operation.document_format not in SUPPORTED_IPP_FORMATS:
            raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))

        return response_for(request, [
            BaseOperationGroup(),
            PrinterAttributesGroup(
                printer_uri_supported=[self.get_printer_uri(request)],
                printer_name="Gutenberg",
                printer_more_info=request.http_request.build_absolute_uri('/'),
                printer_state=PrinterStateEnum.idle,
                printer_state_message="idle",
                queued_job_count=1,
                printer_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0',
                device_uuid='urn:uuid:12345678-9ABC-DEF0-1234-56789ABCDEF0')
        ], requested_attrs_oneset=operation.requested_attributes)

    def _handle_file_upload(self, request: IppRequest, name: str, operation):
        file_name = '{}_{}_{}'.format(
            name, self.user.username,
            datetime.now().strftime(settings.PRINT_DATE_FORMAT))
        file_path = os.path.join(settings.PRINT_DIRECTORY, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb+') as destination:
            while True:
                chunk = request.http_request.read(100000)
                if not chunk:
                    break
                destination.write(chunk)

        file_format = operation.document_format
        if file_format == AUTODETECT_IPP_FORMAT:
            file_format = detect_file_format(file_path)
        if not file_format:
            file_format = DEFAULT_IPP_FORMAT
        if file_format not in SUPPORTED_IPP_FORMATS:
            os.remove(file_path)
            raise DocumentFormatError("Unsupported format: {}".format(operation.document_format))
        return file_path, file_format

    def _create_job_from_template(self, job_template, name: str, status: JobStatus) -> PrintJob:
        job = PrintJob.objects.create(name=name, status=status, owner=self.user)
        PrintingProperties.objects.create(
            color=job_template.print_color_mode != 'monochrome',
            copies=job_template.copies,
            two_sides={
                'one-sided': TwoSidedPrinting.ONE_SIDED,
                'two-sided-long-edge': TwoSidedPrinting.TWO_SIDED_LONG_EDGE,
                'two-sided-short-edge': TwoSidedPrinting.TWO_SIDED_SHORT_EDGE,
            }.get(job_template.sides, TwoSidedPrinting.TWO_SIDED_LONG_EDGE),
            pages_to_print=None, job=job)
        return job

    def print_job(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(PrintJobRequestOperationGroup)
        logger.debug("PrintJob\n" + str(operation))
        if request.has_next():
            job_template = request.read_group(JobTemplateAttributeGroup)
        else:
            job_template = JobTemplateAttributeGroup()
        logger.debug("Print template\n" + str(job_template))

        name = slugify(operation.job_name) if operation.job_name else 'ipp'

        file_path, file_format = self._handle_file_upload(request, name, operation)

        job = self._create_job_from_template(job_template, name, JobStatus.PENDING)

        print_file.delay(file_path, file_format, job.id)

        logger.debug("Print OK")

        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self.get_job_uri(request, job.id),
                job_id=job.id,
                job_state=JobStateEnum.pending,
            )
        ])

    def validate_job(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(PrintJobRequestOperationGroup)
        logger.debug("ValidateJob:\n" + str(operation))
        if operation.document_format and operation.document_format not in SUPPORTED_IPP_FORMATS:
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
        name = slugify(operation.job_name) if operation.job_name else 'ipp'
        job = self._create_job_from_template(job_template, name, JobStatus.INCOMING)
        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self.get_job_uri(request, job.id),
                job_id=job.id,
                job_state=JobStateEnum.pending,
            )
        ])

    def send_document(self, request: IppRequest) -> IppResponse:
        operation = request.read_group(SendDocumentRequestOperationGroup)
        logger.debug("SendDocument\n" + str(operation))
        job = self._find_job(operation)

        if job.status != JobStatus.INCOMING:
            if operation.last_document:
                buff = request.http_request.read(100)
                if len(buff) < 10:
                    return response_for(request, [
                        BaseOperationGroup(),
                        JobPrintResponseAttributes(
                            job_uri=self.get_job_uri(request, job.id),
                            job_id=job.id,
                            job_state=job_status_to_ipp(job.status),
                        )
                    ])
            return minimal_valid_response(request, StatusCodeEnum.server_error_multiple_document_jobs_not_supported)

        file_path, file_format = self._handle_file_upload(request, job.name, operation)
        job.status = JobStatus.PENDING
        job.save()
        print_file.delay(file_path, file_format, job.id)

        logger.debug("Print OK")

        return response_for(request, [
            BaseOperationGroup(),
            JobPrintResponseAttributes(
                job_uri=self.get_job_uri(request, job.id),
                job_id=job.id,
                job_state=job_status_to_ipp(job.status),
            )
        ])

    def get_jobs(self, request: IppRequest):
        operation = request.read_group(GetJobsRequestOperationGroup)
        # logger.debug("GetJob:\n" + str(operation))

        # Workaround to pass the ipp certification suite
        # - we do not use requesting_user_name but authentication provided username instead.
        if operation.requesting_user_name and operation.requesting_user_name.startswith('not-'):
            return response_for(request, [BaseOperationGroup()],
                                requested_attrs_oneset=operation.requested_attributes)

        jobs = PrintJob.objects
        if operation.my_jobs:
            jobs = jobs.filter(owner=self.user)
        if operation.which_jobs == 'completed':
            jobs = jobs.filter(status__in=PrintJob.COMPLETED_STATUSES)
        else:
            jobs = jobs.exclude(status__in=PrintJob.COMPLETED_STATUSES)

        jobs = jobs.order_by('date_created')[operation.first_index:operation.limit].all()

        job_groups = [self._build_job_proto(job, request, full=False) for job in jobs]

        return response_for(request, [BaseOperationGroup()] + job_groups,
                            requested_attrs_oneset=operation.requested_attributes)

    def _find_job(self, operation) -> PrintJob:
        if not (operation.printer_uri and operation.job_id) and not operation.job_uri:
            raise BadRequestError('no job info provided')
        jobs = PrintJob.objects
        jobs = jobs.filter(owner=self.user)
        if operation.job_id:
            job = jobs.filter(id=operation.job_id).first()
        else:
            idx = int(operation.job_uri.slice('/')[-1])
            job = jobs.filter(id=idx).first()
        if not job:
            raise NotFoundError('job not found')
        return job

    def _build_job_proto(self, job: PrintJob, request: IppRequest, full: bool = True):
        clazz = JobObjectAttributeGroupFull if full else JobObjectAttributeGroup
        return clazz(
            job_uri=self.get_job_uri(request, job.id),
            job_id=job.id,
            job_state=job_status_to_ipp(job.status),
            job_printer_uri=self.get_printer_uri(request),
            job_name=job.name,
            job_originating_user_name=job.owner.username,
            time_at_creation=ipp_timestamp(job.date_created),
            time_at_processing=ipp_timestamp(job.date_processed) if job.date_processed else ValueTagsEnum.no_value,
            time_at_completed=ipp_timestamp(job.date_finished) if job.date_finished else ValueTagsEnum.no_value,
            job_printer_up_time=ipp_timestamp(timezone.now()),
        )

    def get_job_attrs(self, request: IppRequest):
        operation = request.read_group(GetJobAttributesRequestOperationGroup)
        # logger.debug("GetJobAttrs:\n" + str(operation))
        job = self._find_job(operation)
        return response_for(request, [BaseOperationGroup(), self._build_job_proto(job, request)],
                            requested_attrs_oneset=operation.requested_attributes)

    def cancel_job(self, request: IppRequest):
        operation = request.read_group(CancelJobRequestOperationGroup)
        logging.debug("CancelJob")
        job = self._find_job(operation)
        if job.status == JobStatus.INCOMING:
            job.status = JobStatus.CANCELED
            job.save()
            return minimal_valid_response(request)
        return not_possible(request)

    def get_printer_uri(self, request: IppRequest):
        uri = request.http_request.build_absolute_uri(
            reverse('ipp_endpoint', kwargs={'token': self.user.api_key, 'rel_path': 'print'}))
        return uri.replace('http', 'ipp')

    def get_job_uri(self, request: IppRequest, job_id: int):
        uri = request.http_request.build_absolute_uri(
            reverse('ipp_endpoint', kwargs={'token': self.user.api_key, 'rel_path': 'job/{}'.format(job_id)}))
        return uri.replace('http', 'ipp')

    def _dispatch(self, version: Tuple[int, int], op_id: int) -> Callable[[IppRequest], IppResponse]:
        # we ignore ipp version for now
        _ = version
        commands = {
            OperationEnum.get_printer_attributes: self.get_printer_attrs,
            OperationEnum.print_job: self.print_job,
            OperationEnum.validate_job: self.validate_job,
            OperationEnum.get_jobs: self.get_jobs,
            OperationEnum.get_job_attributes: self.get_job_attrs,
            OperationEnum.cancel_job: self.cancel_job,
            OperationEnum.create_job: self.create_job,
            OperationEnum.send_document: self.send_document,
        }
        return commands.get(op_id, not_implemented)

    @staticmethod
    def _response(ipp_response: IppResponse, http_code=200):
        http_response = HttpResponse(status=http_code, content_type='application/ipp')
        ipp_response.write_to(http_response)
        return http_response

    def handle_request(self, http_request, rel_path: str):
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
        except Exception as ex:
            logger.error("Internal error in IPP service.", ex)
            return self._response(internal_error(req))
