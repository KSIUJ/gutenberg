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
from django.utils import timezone

from control.models import PrintJob, TwoSidedPrinting, JobStatus, PrinterType
from printing import JobCancelledException
from printing.converter import auto_convert
from printing.postprocess import auto_postprocess

logger = logging.getLogger('gutenberg.worker')


def handle_cancellation(job: PrintJob, handler: Optional[Callable[[], None]] = None):
    # We allow a low possibility of a race condition here as the impact would be negligible
    # (ie. ignored request) and the probability is low.
    job.refresh_from_db()
    if job.status == JobStatus.CANCELING:
        logger.info("Cancelling job {}".format(job))
        if handler:
            handler()
        job.status = JobStatus.CANCELED
        job.status_reason = 'Cancelled by user'
        job.save()
        raise JobCancelledException()


class PrinterBackend(ABC):

    def __init__(self) -> None:
        self.backend_name = self.__class__.__name__

    @abstractmethod
    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        pass

    @abstractmethod
    def submit_job(self, job: PrintJob, file_path: str) -> Any:
        pass

    @abstractmethod
    def cancel_job(self, job: PrintJob, backend_job_id: Any) -> None:
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
            if cnt > 120:
                self.cancel_job(job, backend_job_id)
                raise TimeoutError("Job {} took too long to complete".format(job))
        job.status = JobStatus.COMPLETED
        job.status_reason = ''
        job.finished = timezone.now()
        job.save()


class LocalCupsPrinter(PrinterBackend):
    CUPS_JOB_REQUEST_REGEX = r'^request id is ([^ ]+) '

    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        output = subprocess.check_output(
            ['lpstat', '-l'], stderr=subprocess.STDOUT
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
        output = subprocess.check_output(
            ['lp', file_path] + self._cups_params(job), stderr=subprocess.STDOUT)
        cups_job_id = re.match(self.CUPS_JOB_REQUEST_REGEX, output.decode('utf-8', errors='ignore')).group(1)
        return cups_job_id

    def cancel_job(self, job: PrintJob, backend_job_id: Any):
        subprocess.check_output(['cancel', backend_job_id], stderr=subprocess.STDOUT)


class DisabledPrinter(PrinterBackend):

    def check_status(self, job: PrintJob, backend_job_id: Any) -> bool:
        return False

    def submit_job(self, job: PrintJob, file_path: str):
        job.status = JobStatus.CANCELED
        job.status_reason = "Printer is disabled"
        job.finished = timezone.now()
        job.save()
        raise JobCancelledException()

    def cancel_job(self, job: PrintJob, backend_job_id: Any):
        pass


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
            ext = file_path.lower().rsplit('.', 1)[-1]
            tmp_input = os.path.join(tmpdir, 'input.' + ext)
            shutil.copyfile(file_path, os.path.join(tmpdir, 'input.' + ext))
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
            }.get(job.printer.printer_type, PrinterType.DISABLED)()
            backend.print(job, out)
    except JobCancelledException:
        # Cancelling job
        pass
    except Exception as ex:
        job.status = JobStatus.ERROR
        job.status_reason = repr(ex)
        if hasattr(ex, 'output') and isinstance(ex.output, bytes):
            job.status_reason += '\nOutput:\n' + ex.output.decode('utf-8', errors='ignore')
        job.save()
        raise ex
