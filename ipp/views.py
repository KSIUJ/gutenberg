import base64
from datetime import datetime, timezone
from typing import Optional, Tuple, Any, List

from django.http import HttpResponse, HttpRequest
from django.template.defaultfilters import slugify
from django.templatetags.static import static
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

import printing
from common.models import User
from control.models import Printer, TwoSidedPrinting, PrintJob, JobStatus
from ipp.constants import JobStateEnum, ValueTagsEnum
from ipp.exceptions import NotPossibleError, DocumentFormatError
from ipp.proto import IppRequest, ipp_timestamp, AttributeGroup, IppResponse
from ipp.proto_operations import JobObjectAttributeGroupFull, JobObjectAttributeGroup
from ipp.service import BaseIppEverywhereService
from printing.printing import create_print_job, submit_print_job
from printing.utils import SUPPORTED_IPP_FORMATS, DEFAULT_IPP_FORMAT


class GutenbergIppService(BaseIppEverywhereService):
    def __init__(self, printer, user: User, is_secure: bool, basic_auth: bool, base_uri: str,
                 printer_icon: str, webpage_uri: str) -> None:
        self.user = user
        self.printer = printer
        self.base_uri = base_uri

        printer_uri = f'{base_uri}print'
        color_allowed = printer.color_allowed
        duplex = printer.duplex_supported

        super().__init__(actor_name=user.username,
                         printer_name=printer.name,
                         printer_uri=printer_uri,
                         printer_tls=is_secure,
                         printer_basic_auth=basic_auth,
                         printer_color=color_allowed,
                         printer_duplex=duplex,
                         printer_icon=printer_icon,
                         supported_ipp_formats=SUPPORTED_IPP_FORMATS,
                         default_ipp_format=DEFAULT_IPP_FORMAT,
                         webpage_uri=webpage_uri)

    @staticmethod
    def _job_status_to_ipp(status):
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

    def _create_job(self, operation, job_template) -> int:
        name = slugify(operation.job_name) if operation.job_name else 'ipp'
        pages_to_print = None
        if job_template.page_ranges:
            pages_to_print = ','.join(['{}-{}'.format(x.lower, x.upper) for x in job_template.page_ranges])
        two_sided = {
            'one-sided': TwoSidedPrinting.ONE_SIDED,
            'two-sided-long-edge': TwoSidedPrinting.TWO_SIDED_LONG_EDGE,
            'two-sided-short-edge': TwoSidedPrinting.TWO_SIDED_SHORT_EDGE,
        }.get(job_template.sides,
              TwoSidedPrinting.TWO_SIDED_LONG_EDGE) if self.printer.duplex_supported else \
            TwoSidedPrinting.ONE_SIDED
        return create_print_job(
            user=self.user,
            printer=self.printer,
            job_name=name,
            pages_to_print=pages_to_print,
            color=job_template.print_color_mode != 'monochrome' and self.printer.color_allowed,
            copies=job_template.copies,
            two_sided=two_sided,
        )

    def _submit_job(self, request: IppRequest, operation, job_id) -> int:
        try:
            return submit_print_job(
                document_buffer=request.http_request,
                user=self.user,
                document_type=operation.document_format,
                job_id=job_id
            )
        except printing.utils.DocumentFormatError as ex:
            raise DocumentFormatError(ex)

    def _get_job_uri(self, job_id) -> str:
        return f'{self.base_uri}job/{job_id}'

    def _get_job(self, job_id) -> Optional[Tuple[int, JobStateEnum, bool, Any]]:
        jobs = PrintJob.objects
        jobs = jobs.filter(owner=self.user, printer=self.printer)
        job = jobs.filter(id=job_id).first()
        if not job:
            return None
        return job.id, self._job_status_to_ipp(job.status), job.status != JobStatus.INCOMING, job

    def _get_jobs(self, first_index: int, limit: int, all_jobs: bool = False,
                  exclude_completed: bool = True) -> List[Any]:
        jobs = PrintJob.objects.filter(owner=self.user, printer=self.printer)
        if all_jobs:
            pass
        elif exclude_completed:
            jobs = jobs.exclude(status__in=PrintJob.COMPLETED_STATUSES)
        else:
            jobs = jobs.filter(status__in=PrintJob.COMPLETED_STATUSES)
        jobs = jobs.order_by('date_created')[first_index:limit].all()
        return jobs

    def _build_job_proto(self, job: Any, full_job_proto: bool = True) -> AttributeGroup:
        clazz = JobObjectAttributeGroupFull if full_job_proto else JobObjectAttributeGroup
        return clazz(
            job_uri=self._get_job_uri(job.id),
            job_id=job.id,
            job_state=self._job_status_to_ipp(job.status),
            job_printer_uri=self.printer_uri,
            job_name=job.name,
            job_originating_user_name=job.owner.username,
            time_at_creation=ipp_timestamp(job.date_created.astimezone(timezone.utc)),
            time_at_processing=ipp_timestamp(
                job.date_processed.astimezone(timezone.utc)) if job.date_processed else ValueTagsEnum.no_value,
            time_at_completed=ipp_timestamp(
                job.date_finished.astimezone(timezone.utc)) if job.date_finished else ValueTagsEnum.no_value,
            job_printer_up_time=ipp_timestamp(datetime.now(tz=timezone.utc)),
        )

    def _cancel_job(self, job: Any) -> None:
        rows = PrintJob.objects.filter(id=job.id).exclude(status__in=PrintJob.COMPLETED_STATUSES).update(
            status=JobStatus.CANCELING)
        if rows == 0:
            raise NotPossibleError('no jobs cancelled')

    def _http_response(self, ipp_response: IppResponse, http_code=200):
        http_response = HttpResponse(status=http_code, content_type='application/ipp')
        ipp_response.write_to(http_response)
        return http_response


class IppView(View):
    http_method_names = ['get', 'post', 'options']
    BASIC_AUTH_TOKEN = 'basic'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, rel_path: str, *args, **kwargs):
        if rel_path == '':
            return HttpResponse(b'This is gutenberg ipp-server', content_type='text/plain')
        else:
            return HttpResponse(b'Page does not exist', status=404, content_type='text/plain')

    def _authenticate(self, request: HttpRequest, token):
        user = None
        basic_auth = token == self.BASIC_AUTH_TOKEN
        if basic_auth:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            token_type, _, credentials = auth_header.partition(' ')
            if token_type.lower() == 'basic':
                username, password = base64.b64decode(credentials).decode('utf-8', errors='ignore').split(':')
                if password:
                    user = User.objects.filter(username=username, api_key=password).first()
        elif token:
            user = User.objects.filter(api_key=token).first()
        if not user:
            if basic_auth:
                res = HttpResponse(b'Unauthorized', status=401, content_type='text/plain')
                res['WWW-Authenticate'] = 'Basic realm="gutenberg", charset="UTF-8"'
                return res
            else:
                return HttpResponse(b'Forbidden', status=403, content_type='text/plain')
        return user, basic_auth

    def post(self, request: HttpRequest, printer_id, token, rel_path, *args, **kwargs):
        user, basic_auth = self._authenticate(request, token)
        printer = Printer.get_printer_for_user(user, printer_id)
        if not printer:
            return HttpResponse(b'Not found', status=404, content_type='text/plain')
        base_endpoint_url = request.build_absolute_uri(
            reverse('ipp_endpoint', kwargs={'printer_id': printer.id, 'token': token, 'rel_path': ''})
        ).replace('http', 'ipp')
        printer_icon = request.build_absolute_uri(static('img/logo-128.png'))
        webpage_uri = request.build_absolute_uri('/')
        service = GutenbergIppService(printer, user, request.is_secure(), basic_auth, base_endpoint_url, printer_icon,
                                      webpage_uri)
        return service.handle_request(request, rel_path)
