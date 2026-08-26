import logging
import re
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from control.models import GutenbergJob, TwoSidedPrinting, JobStatus
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
    def submit_job(self, job: GutenbergJob, file_path: str) -> Any:
        """Submit the job to the backend. Returns an object used by backend to identify the job (e.g. job id string)"""
        pass

    @abstractmethod
    def cancel_job(self, job: GutenbergJob, backend_job_id: Any) -> None:
        """Attempt canceling processing the job on backend."""
        pass

    def print(self, job: GutenbergJob, file_path: str, is_manual_second_pass: bool = False):
        logger.info("Printing job {} via {}".format(job, self.backend_name))

        # Check if manual duplex is required (no hardware duplex support)
        is_manual_duplex = (
            job.properties.two_sides != TwoSidedPrinting.ONE_SIDED and
            not job.printer.duplex_supported
        )

        # Select the file to print based on the pass
        if is_manual_duplex and not is_manual_second_pass:
            file_to_print, _ = job.get_manual_duplex_files()
        elif is_manual_duplex and is_manual_second_pass:
            _, file_to_print = job.get_manual_duplex_files()
        else:
            file_to_print = file_path

        # Submit job to the CUPS backend
        backend_job_id = self.submit_job(job, file_to_print)
        job.backend_job_id = backend_job_id
        job.save()

        # Monitor print completion with cancellation and timeout handling
        cnt = 0
        try:
            while self.check_status(job, backend_job_id):
                logger.info("Job {} is still printing via {}".format(job, self.backend_name))
                handle_cancellation(job, lambda: self.cancel_job(job, backend_job_id))
                time.sleep(1)
                cnt += 1
                if cnt > PRINTING_TIMEOUT_S:
                    self.cancel_job(job, backend_job_id)
                    raise TimeoutError("Job {} took too long to complete".format(job))
        except JobCanceledException:
            logger.warning("Job {} processing stopped because it was canceled".format(job))
            return

        # Update status based on execution phase
        if is_manual_duplex and not is_manual_second_pass:
            # First pass completed (odd pages); wait for user action
            job.status = JobStatus.WAITING_FOR_USER
            job.status_reason = "Manual Duplex: Turn pages over and place them back in the feeder, then click Continue."
            job.save()
        else:
            # Second pass or standard printing completed
            job.status = JobStatus.COMPLETED
            job.status_reason = ''
            job.date_finished = timezone.now()
            job.save()


class LocalCupsPrinter(PrinterBackend):
    common_options = ['-h', settings.CUPS_SERVERNAME]
    ipp_capabilities_test = Path(__file__).with_name('ipptool') / 'get-printer-capabilities.test'

    @staticmethod
    def _parse_lpoptions(output: str) -> dict[str, list[str]]:
        """Return the available values for each option from ``lpoptions -l`` output."""
        options = {}
        for line in output.splitlines():
            match = re.match(r'^(?P<name>[^/\s:]+)(?:/[^:]+)?:\s*(?P<values>.*)$', line)
            if not match:
                continue
            options[match.group('name')] = [value.lstrip('*') for value in match.group('values').split()]
        return options

    @staticmethod
    def _parse_ipptool_attributes(output: str) -> dict[str, list[str]]:
        """Extract the requested simple IPP attributes from ``ipptool -tv`` output."""
        attributes = {}
        for line in output.splitlines():
            match = re.match(r'^\s*(?P<name>[\w-]+) \([^)]*\) = (?P<values>.*)$', line)
            if not match:
                continue
            attributes[match.group('name')] = [value.strip() for value in match.group('values').split(',')]
        return attributes

    @staticmethod
    def _get_cups_printer_uri(cups_printer_name: str) -> str | None:
        output = subprocess.check_output(
            ['lpstat'] + LocalCupsPrinter.common_options + ['-v', cups_printer_name],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=TASK_TIMEOUT_S,
            )
        match = re.search(r'^device for [^:]+:\s*(?P<uri>\S+)$', output, re.MULTILINE)
        return match.group('uri') if match else None

    @staticmethod
    def _option_value(options: dict[str, list[str]], option_names: tuple[str, ...],
                      values: tuple[str, ...]) -> str | None:
        """Find a CUPS option and value without changing CUPS' original spelling."""
        for option_name in option_names:
            available_values = options.get(option_name, [])
            value_by_normalized_name = {value.casefold(): value for value in available_values}
            for value in values:
                if selected := value_by_normalized_name.get(value.casefold()):
                    # IPP capability attributes end in ``-supported`` while
                    # CUPS expects the corresponding job-template attribute.
                    return f'{option_name.removesuffix("-supported")}={selected}'
        return None

    @staticmethod
    def _configuration_from_options(cups_printer_name: str,
                                    options: dict[str, list[str]]) -> dict[str, str | bool | None]:
        """Map CUPS or IPP capabilities to the fields Gutenberg currently supports."""
        color_option_names = ('print-color-mode-supported', 'print-color-mode', 'ColorModel', 'ColorMode',
                              'OutputMode')
        grayscale_param = LocalCupsPrinter._option_value(
            options, color_option_names, ('monochrome', 'mono', 'gray', 'grey', 'black'))
        color_param = LocalCupsPrinter._option_value(
            options, color_option_names, ('color', 'rgb', 'cmyk'))
        one_sided_param = LocalCupsPrinter._option_value(
            options, ('sides-supported', 'sides'), ('one-sided',))
        two_sided_long_edge_param = LocalCupsPrinter._option_value(
            options, ('sides-supported', 'sides'), ('two-sided-long-edge',))
        two_sided_short_edge_param = LocalCupsPrinter._option_value(
            options, ('sides-supported', 'sides'), ('two-sided-short-edge',))
        # Older PPD-based CUPS queues commonly use these names instead of
        # the IPP-standard ``sides`` option.
        if one_sided_param is None:
            one_sided_param = LocalCupsPrinter._option_value(options, ('Duplex',), ('None',))
        if two_sided_long_edge_param is None:
            two_sided_long_edge_param = LocalCupsPrinter._option_value(
                options, ('Duplex',), ('DuplexNoTumble',))
        if two_sided_short_edge_param is None:
            two_sided_short_edge_param = LocalCupsPrinter._option_value(
                options, ('Duplex',), ('DuplexTumble',))

        return {
            'cups_printer_name': cups_printer_name,
            'color_supported': 'true' in {value.casefold() for value in options.get('color-supported', [])} or
                               color_param is not None,
            # Gutenberg's current boolean model advertises both duplex modes.
            'duplex_supported': two_sided_long_edge_param is not None and two_sided_short_edge_param is not None,
            'print_grayscale_param': grayscale_param,
            'print_color_param': color_param,
            'print_one_sided_param': one_sided_param,
            'print_two_sided_long_edge_param': two_sided_long_edge_param,
            'print_two_sided_short_edge_param': two_sided_short_edge_param,
        }

    @staticmethod
    def get_cups_printer_options(cups_printer_name: str) -> dict[str, str | bool | None]:
        """Discover the subset of CUPS options Gutenberg can configure for a queue.

        The result deliberately mirrors ``LocalPrinterParams`` rather than exposing
        every driver-specific CUPS option. Driverless queues are queried through
        IPP; PPD-based queues fall back to ``lpoptions -l``.
        """
        try:
            printer_uri = LocalCupsPrinter._get_cups_printer_uri(cups_printer_name)
            if printer_uri and printer_uri.startswith(('ipp://', 'ipps://')):
                output = subprocess.check_output(
                    # ``-t`` reports the test result and ``-v`` includes the
                    # response attributes which we parse below.
                    ['ipptool', '-tv', printer_uri, str(LocalCupsPrinter.ipp_capabilities_test)],
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=TASK_TIMEOUT_S,
                )
                options = LocalCupsPrinter._parse_ipptool_attributes(output)
                if any(name in options for name in ('color-supported', 'print-color-mode-supported',
                                                    'sides-supported')):
                    return LocalCupsPrinter._configuration_from_options(cups_printer_name, options)
                logger.warning("IPP capability query for CUPS printer %s returned no supported options",
                               cups_printer_name)
        except Exception as error:
            logger.warning("Failed to query IPP capabilities for CUPS printer %s: %s", cups_printer_name, error,
                           exc_info=True)

        try:
            output = subprocess.check_output(
                ['lpoptions'] + LocalCupsPrinter.common_options + ['-p', cups_printer_name, '-l'],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=TASK_TIMEOUT_S,
                )
        except Exception as error:
            logger.error("Failed to get options for CUPS printer %s: %s", cups_printer_name, error,
                         exc_info=True)
            return {}

        options = LocalCupsPrinter._parse_lpoptions(output)
        if not options:
            logger.error("CUPS returned no options for printer %s", cups_printer_name)
            return {}
        return LocalCupsPrinter._configuration_from_options(cups_printer_name, options)

    @staticmethod
    def parse_lpstat_job_status(output: str, backend_job_id: Any) -> str | None:
        """
        Parses `lpstat` multi-line text output to extract status attributes for a specific job.
        In `lpstat -l` output, job metadata is indented under the primary job header line
        for example 'PDF-5 ...'. We collect all indented lines immediately following
        the matching job ID until an unindented line or EOF is encountered.
        Returns None if job_id is not found in the output.
        """
        lines = output.splitlines()
        job_pattern = re.compile(f"^{re.escape(str(backend_job_id))}\\s")

        for idx, line in enumerate(lines):
            if job_pattern.match(line):
                status_lines = []
                for i in range(idx + 1, len(lines)):
                    if re.match(r'^\s+', lines[i]):
                        status_lines.append(lines[i].strip())
                    else:
                        break
                return '\n'.join(status_lines)

        return None

    def check_status(self, job: GutenbergJob, backend_job_id: Any) -> bool:
        """
        Checks the status of a print job in CUPS. Returns True if the job is still in progress, False if it has completed or been canceled.
        Raises `JobCanceledException` if the job was canceled or disappeared from CUPS without completing successfully.
        """
        active_output = subprocess.check_output(
            ['lpstat'] + self.common_options + ['-l'],
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
            ).decode('utf-8', errors='ignore')

        status = self.parse_lpstat_job_status(active_output, backend_job_id)
        if status is not None:
            GutenbergJob.objects.filter(id=job.id).update(status_reason=status)
            return True

        # By default, running `lpstat` without `-W` only checks active (not-completed) jobs.
        # If the job is no longer active, we query all jobs (`-W all`) to check
        # if it finished or disappeared from the queue.
        # Reference: https://www.cups.org/doc/man-lpstat.html (-W which-jobs option)
        all_output = subprocess.check_output(
            ['lpstat'] + self.common_options + ['-W','all','-l'],
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
            ).decode('utf-8', errors='ignore')

        status = self.parse_lpstat_job_status(all_output, backend_job_id)
        if status is not None:
            GutenbergJob.objects.filter(id=job.id).update(status_reason=status)
            # Check for the standard IPP 'job-state-reasons' attribute indicating success.
            # CUPS sets this when a job finishes without errors.
            # Reference: https://datatracker.ietf.org/doc/html/rfc8011#section-5.3.8
            if 'job-completed-successfully' in status.lower():
                return False

        # If the job is missing from both active queue and history without completion flags,
        # CUPS treated it as canceled.
        job.status = JobStatus.CANCELED
        job.status_reason = 'Job disappeared from CUPS queue'
        job.date_finished = timezone.now()
        job.save()
        raise JobCanceledException("Job was canceled in CUPS")

    @staticmethod
    def _cups_params(job: GutenbergJob):
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
        return options

    def submit_job(self, job: GutenbergJob, file_path: str) -> Any:
        cups_name = job.printer.localprinterparams.cups_printer_name
        output = subprocess.check_output(
            ['lp'] + self.common_options + [file_path] + self._cups_params(job),
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
            ).decode('utf-8', errors='ignore')
        mt = re.search(re.escape(cups_name) + r'-([^ ]+)', output)
        if mt:
            return '{0}-{1}'.format(cups_name, mt.group(1))
        raise ValueError('Invalid lp output: {}'.format(output))

    def cancel_job(self, job: GutenbergJob, backend_job_id: Any):
        subprocess.check_output(
            ['cancel'] + self.common_options + [backend_job_id],
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
            )


class DisabledPrinter(PrinterBackend):

    def check_status(self, job: GutenbergJob, backend_job_id: Any) -> bool:
        return False

    def submit_job(self, job: GutenbergJob, file_path: str):
        job.status = JobStatus.CANCELED
        job.status_reason = "Printer is disabled"
        job.date_finished = timezone.now()
        job.save()
        raise JobCanceledException()

    def cancel_job(self, job: GutenbergJob, backend_job_id: Any):
        pass
