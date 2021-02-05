import datetime
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any

from celery import shared_task
from django.conf import settings
from django.db.models.functions import Greatest, Coalesce
from django.utils import timezone

from control.models import PrintJob, TwoSidedPrinting, JobStatus, PrinterType, Printer, PrintingProperties
from printing.converter import auto_convert, detect_file_format
from printing.postprocess import auto_postprocess
from printing.utils import JobCanceledException, TASK_TIMEOUT_S, PRINTING_TIMEOUT_S, DEFAULT_IPP_FORMAT, \
    AUTODETECT_IPP_FORMAT, SUPPORTED_IPP_FORMATS, DocumentFormatError

logger = logging.getLogger('gutenberg.worker')


def handle_cancellation(job: PrintJob, handler: Optional[Callable[[], None]] = None):
    # We allow a low possibility of a race condition here as the impact would be negligible
    # (ie. ignored request) and the probability is low.
    job.refresh_from_db()
    if job.status == JobStatus.CANCELING:
        logger.info("Canceling job {}".format(job))
        if handler:
            handler()
        job.status = JobStatus.CANCELED
        job.status_reason = 'Canceled by user'
        job.save()
        raise JobCanceledException()


class PrinterBackend(ABC):

    def __init__(self) -> None:
        self.backend_name = self.__class__.__name__

    @abstractmethod
    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        """Checks if the backend has finished processing the job. Returns `true` on finish."""
        pass

    @abstractmethod
    def submit_job(self, job: PrintJob, file_path: str) -> Any:
        """Submit the job to the backend. Returns an object used by backend to identify the job (e.g. job id string)"""
        pass

    @abstractmethod
    def cancel_job(self, job: PrintJob, backend_job_id: Any) -> None:
        """Attempt canceling processing the job on backend."""
        pass

    def print(self, job: PrintJob, file_path: str):
        logger.info("Printing job {} via {}".format(job, self.backend_name))
        backend_job_id = self.submit_job(job, file_path)
        cnt = 0
        while self.check_status(job, backend_job_id):
            logger.info("Job {} is still printing via {}".format(job, self.backend_name))
            handle_cancellation(job, lambda: self.cancel_job(job, backend_job_id))
            time.sleep(1)
            cnt += 1
            if cnt > PRINTING_TIMEOUT_S:
                self.cancel_job(job, backend_job_id)
                raise TimeoutError("Job {} took too long to complete".format(job))
        job.status = JobStatus.COMPLETED
        job.status_reason = ''
        job.finished = timezone.now()
        job.save()


class LocalCupsPrinter(PrinterBackend):
    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        output = subprocess.check_output(
            ['lpstat', '-l'], stderr=subprocess.STDOUT, timeout=TASK_TIMEOUT_S
        )
        output_lines = output.decode('utf-8', errors='ignore').splitlines()
        for idx, val in enumerate(output_lines):
            if not re.match('^{}\\s'.format(backend_job_id), val):
                continue
            max_idx = idx
            for i in range(idx + 1, len(output_lines)):
                if re.match(r'^\s+', output_lines[i]):
                    max_idx = i
                else:
                    break
            status = '\n'.join(x.strip() for x in output_lines[idx + 1: max_idx + 1])
            PrintJob.objects.filter(id=job.id).update(status_reason=status)
            return True
        return False

    @staticmethod
    def _cups_params(job: PrintJob):
        options = ['-d', job.printer.localprinterparams.cups_printer_name]
        options += ['-n', str(job.properties.copies)]
        params = job.printer.localprinterparams
        if job.printer.color_supported:
            color_opt = params.print_color_param if job.properties.color else params.print_grayscale_param
            if color_opt:
                options += ['-o', color_opt]
        if job.printer.duplex_supported:
            two_sided_opt = {
                TwoSidedPrinting.ONE_SIDED: params.print_one_sided_param,
                TwoSidedPrinting.TWO_SIDED_LONG_EDGE: params.print_two_sided_long_edge_param,
                TwoSidedPrinting.TWO_SIDED_SHORT_EDGE: params.print_two_sided_short_edge_param,
            }.get(job.properties.two_sides, None)
            if two_sided_opt:
                options += ['-o', two_sided_opt]
        options += ['-o', 'fit-to-page']
        return options

    def submit_job(self, job: PrintJob, file_path: str) -> Any:
        cups_name = job.printer.localprinterparams.cups_printer_name
        output = subprocess.check_output(
            ['lp', file_path] + self._cups_params(job), stderr=subprocess.STDOUT, timeout=TASK_TIMEOUT_S).decode(
            'utf-8', errors='ignore')
        mt = re.search(re.escape(cups_name) + r'-([^ ]+)', output)
        if mt:
            return '{0}-{1}'.format(cups_name, mt.group(1))
        raise ValueError('Invalid lp output: {}'.format(output))

    def cancel_job(self, job: PrintJob, backend_job_id: Any):
        subprocess.check_output(['cancel', backend_job_id], stderr=subprocess.STDOUT, timeout=TASK_TIMEOUT_S)


class DisabledPrinter(PrinterBackend):

    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        return False

    def submit_job(self, job: PrintJob, file_path: str):
        job.status = JobStatus.CANCELED
        job.status_reason = "Printer is disabled"
        job.finished = timezone.now()
        job.save()
        raise JobCanceledException()

    def cancel_job(self, job: PrintJob, backend_job_id: Any):
        pass


def create_print_job(user: settings.AUTH_USER_MODEL,
                     printer: Printer,
                     job_name: Optional[str] = None,
                     pages_to_print: Optional[str] = None,
                     color: bool = False,
                     copies: int = 1,
                     two_sided: TwoSidedPrinting = TwoSidedPrinting.ONE_SIDED):
    job = PrintJob.objects.create(name=job_name, status=JobStatus.INCOMING, owner=user, printer=printer)
    PrintingProperties.objects.create(
        color=color,
        copies=copies,
        two_sides=two_sided,
        pages_to_print=pages_to_print,
        job=job)
    return job.id


def submit_print_job(document_buffer,
                     job_id,
                     user: settings.AUTH_USER_MODEL,
                     document_type: Optional[str] = None):
    job = PrintJob.objects.filter(id=job_id).first()
    file_name = '{}_{}_{}'.format(
        job.name, user.username,
        timezone.now().strftime(settings.PRINT_DATE_FORMAT))
    file_path = os.path.join(settings.PRINT_DIRECTORY, file_name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb+') as destination:
        while True:
            chunk = document_buffer.read(100000)
            if not chunk:
                break
            destination.write(chunk)

    file_format = document_type
    if not file_format:
        file_format = DEFAULT_IPP_FORMAT
    if file_format == AUTODETECT_IPP_FORMAT:
        file_format = detect_file_format(file_path)
    if file_format not in SUPPORTED_IPP_FORMATS:
        os.remove(file_path)
        raise DocumentFormatError("Unsupported format: {}".format(file_format))

    job.status = JobStatus.PENDING
    job.save()
    print_file.delay(file_path, file_format, job_id)
    return job_id


@shared_task
def print_file(file_path, file_format, job_id):
    job = PrintJob.objects.filter(id=job_id).first()
    if not job:
        logger.warning("Job id {} missing.".format(job_id))
        return
    logger.info("Processing job {}".format(job))
    handle_cancellation(job)
    job.status = JobStatus.PROCESSING
    job.status_reason = ''
    job.save()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = os.path.splitext(file_path)[1].lower()
            if not ext:
                ext = '.bin'
            tmp_input = os.path.join(tmpdir, 'input' + ext)
            shutil.copyfile(file_path, tmp_input)
            out, out_type = auto_convert(tmp_input, file_format, tmpdir)
            handle_cancellation(job)
            out, num_pages = auto_postprocess(out, out_type, tmpdir, job)
            handle_cancellation(job)
            job.status = JobStatus.PRINTING
            job.status_reason = ''
            job.date_processed = timezone.now()
            job.pages = num_pages * job.properties.copies
            job.save()
            backend = {
                PrinterType.DISABLED: DisabledPrinter,
                PrinterType.LOCAL_CUPS: LocalCupsPrinter,
            }.get(job.printer.printer_type, DisabledPrinter)()
            backend.print(job, out)
    except JobCanceledException:
        # Canceling job
        pass
    except Exception as ex:
        job.status = JobStatus.ERROR
        job.status_reason = repr(ex)
        if hasattr(ex, 'output') and isinstance(ex.output, bytes):
            job.status_reason += '\nOutput:\n' + ex.output.decode('utf-8', errors='ignore')
        job.save()
        raise ex


@shared_task
def cleanup_print_jobs():
    stale_jobs = PrintJob.objects.exclude(status__in=PrintJob.COMPLETED_STATUSES).annotate(
        last_activity=Greatest('date_created', Coalesce('date_processed', 0), Coalesce(0, 'date_finished'))).filter(
        last_activity__lt=timezone.now() - datetime.timedelta(seconds=2 * TASK_TIMEOUT_S))
    stale_jobs.update(status=JobStatus.ERROR,
                      status_reason='This task has expired. There is most likely an issue with Gutenberg background '
                                    'workers. Please notify administrators about this.')
