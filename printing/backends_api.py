import logging
import re
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any

from django.utils import timezone

from control.models import GutenbergJob, TwoSidedPrinting, JobStatus, JobArtefact
from printing.utils import JobCanceledException, TASK_TIMEOUT_S, PRINTING_TIMEOUT_S, handle_cancellation

logger = logging.getLogger('gutenberg.worker')


class PrinterBackend(ABC):

    def __init__(self) -> None:
        self.backend_name = self.__class__.__name__

    @abstractmethod
    def check_status(self, job: GutenbergJob, backend_job_id: Any) -> bool:
        """Checks if the backend has finished processing the job. Returns `true` on finish."""
        pass

    @abstractmethod
    def submit_job(self, job: GutenbergJob, file_path: str, artifact:JobArtefact) -> Any:
        """Submit the job to the backend. Returns an object used by backend to identify the job (e.g. job id string)"""
        pass

    @abstractmethod
    def cancel_job(self, job: GutenbergJob, backend_job_id: Any) -> None:
        """Attempt canceling processing the job on backend."""
        pass

    def print(self, job: GutenbergJob, file_path: str, artefact:JobArtefact):
        logger.info("Printing job {} via {}".format(job, self.backend_name))
        backend_job_id = self.submit_job(job, file_path, artefact)
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
        job.date_finished = timezone.now()
        job.save()


class LocalCupsPrinter(PrinterBackend):
    def check_status(self, job: GutenbergJob, backend_job_id: Any) -> bool:
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
            GutenbergJob.objects.filter(id=job.id).update(status_reason=status)
            return True
        return False

    @staticmethod
    def _cups_params(job: GutenbergJob, artifact:JobArtefact):
        options = ['-d', job.printer.localprinterparams.cups_printer_name]
        options += ['-n', str(artifact.properties.copies)]
        params = job.printer.localprinterparams
        if job.printer.color_supported:
            color_opt = params.print_color_param if artifact.properties.color else params.print_grayscale_param
            if color_opt:
                options += ['-o', color_opt]
        if job.printer.duplex_supported:
            two_sided_opt = {
                TwoSidedPrinting.ONE_SIDED: params.print_one_sided_param,
                TwoSidedPrinting.TWO_SIDED_LONG_EDGE: params.print_two_sided_long_edge_param,
                TwoSidedPrinting.TWO_SIDED_SHORT_EDGE: params.print_two_sided_short_edge_param,
            }.get(artifact.properties.two_sides, None)
            if two_sided_opt:
                options += ['-o', two_sided_opt]
        if artifact.properties.fit_to_page:
            options += ['-o', 'fit-to-page']
        else:
            options += ['-o', 'nofit-to-page']
        return options

    def submit_job(self, job: GutenbergJob, file_path: str, artifact:JobArtefact) -> Any:
        cups_name = job.printer.localprinterparams.cups_printer_name
        output = subprocess.check_output(
            ['lp', file_path] + self._cups_params(job, artifact), stderr=subprocess.STDOUT, timeout=TASK_TIMEOUT_S).decode(
            'utf-8', errors='ignore')
        mt = re.search(re.escape(cups_name) + r'-([^ ]+)', output)
        if mt:
            return '{0}-{1}'.format(cups_name, mt.group(1))
        raise ValueError('Invalid lp output: {}'.format(output))

    def cancel_job(self, job: GutenbergJob, backend_job_id: Any):
        subprocess.check_output(['cancel', backend_job_id], stderr=subprocess.STDOUT, timeout=TASK_TIMEOUT_S)


class DisabledPrinter(PrinterBackend):

    def check_status(self, job: GutenbergJob, backend_job_id: Any) -> bool:
        return False

    def submit_job(self, job: GutenbergJob, file_path: str, artifact:JobArtefact):
        job.status = JobStatus.CANCELED
        job.status_reason = "Printer is disabled"
        job.date_finished = timezone.now()
        job.save()
        raise JobCanceledException()

    def cancel_job(self, job: GutenbergJob, backend_job_id: Any):
        pass
