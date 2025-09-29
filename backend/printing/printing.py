import datetime
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db.models.functions import Greatest, Coalesce
from django.utils import timezone

from control.models import GutenbergJob, TwoSidedPrinting, JobStatus, PrinterType, Printer, PrintingProperties, \
    JobArtefact, JobArtefactType
from printing.backends import DisabledPrinter, LocalCupsPrinter
from printing.converter import detect_file_format, get_converter
from printing.postprocess import FinalPageProcessor, NoPagesToPrintException
from printing.processing.imposition_templates import StandardImpositionTemplate
from printing.processing.pages import PageSize
from printing.utils import JobCanceledException, TASK_TIMEOUT_S, DEFAULT_IPP_FORMAT, \
    AUTODETECT_IPP_FORMAT, SUPPORTED_IPP_FORMATS, DocumentFormatError, handle_cancellation

logger = logging.getLogger('gutenberg.worker')


def create_print_job(user: settings.AUTH_USER_MODEL,
                     printer: Printer,
                     job_name: Optional[str] = None,
                     pages_to_print: Optional[str] = None,
                     color: bool = False,
                     copies: int = 1,
                     two_sided: TwoSidedPrinting = TwoSidedPrinting.ONE_SIDED):
    job = GutenbergJob.objects.create(name=job_name, status=JobStatus.INCOMING, owner=user, printer=printer)
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
    job = GutenbergJob.objects.filter(id=job_id).first()

    with tempfile.TemporaryFile() as tmp:
        while True:
            chunk = document_buffer.read(100000)
            if not chunk:
                break
            tmp.write(chunk)
        artefact = JobArtefact.objects.create(job=job, artefact_type=JobArtefactType.SOURCE, file=File(tmp))

    file_format = document_type
    if not file_format:
        file_format = DEFAULT_IPP_FORMAT
    if file_format == AUTODETECT_IPP_FORMAT:
        file_format = detect_file_format(artefact.file.path)
    if file_format not in SUPPORTED_IPP_FORMATS:
        artefact.delete()
        job.status = JobStatus.ERROR
        job.status_reason = 'Unsupported file format: {}'.format(file_format)
        job.save()
        raise DocumentFormatError("Unsupported format: {}".format(file_format))
    artefact.mime_type = file_format
    artefact.save()

    job.status = JobStatus.PENDING
    job.save()
    print_file.delay(job_id)
    return job_id


def _no_pages_cancel(job):
    job.status = JobStatus.CANCELED
    job.status_reason = 'No pages to print. Check your pages filter expression.'
    job.save()
    raise JobCanceledException()


@shared_task
def print_file(job_id):
    job = GutenbergJob.objects.filter(id=job_id).first()
    if not job:
        logger.warning("Job id {} missing.".format(job_id))
        return
    logger.info("Processing job {}".format(job))
    handle_cancellation(job)
    job.status = JobStatus.PROCESSING
    job.status_reason = ''
    job.save()
    try:
        with (tempfile.TemporaryDirectory() as job_tmpdir):
            sum_num_pages = 0
            for idx, artefact in enumerate(job.artefacts.filter(artefact_type=JobArtefactType.SOURCE)):
                with tempfile.TemporaryDirectory() as artefact_tmpdir:
                    file_path = artefact.file.path
                    file_format = artefact.mime_type
                    ext = os.path.splitext(file_path)[1].lower()
                    if not ext:
                        ext = '.bin'
                    tmp_input = os.path.join(artefact_tmpdir, 'input' + ext)
                    shutil.copyfile(file_path, tmp_input)

                    conv = get_converter(file_format, artefact_tmpdir, job.properties.fit_to_page)
                    preprocess_result = conv.preprocess(tmp_input)
                    handle_cancellation(job)

                    imposition_template = StandardImpositionTemplate(media_size=PageSize(width_mm=210, height_mm=297), work_dir=artefact_tmpdir)
                    # TODO: Support `orientation_requested` IPP attribute
                    input_page_orientation = preprocess_result.orientation
                    # TODO: Use the N-up setting
                    final_page_processor = FinalPageProcessor(artefact_tmpdir, job.properties.n_up, imposition_template.get_final_page_sizes(), input_page_orientation)

                    input_pages_file = conv.create_input_pages(preprocess_result, final_page_processor.input_page_size)
                    handle_cancellation(job)

                    try:
                        final_pages_file = final_page_processor.create_final_pages(input_pages_file, job.properties.pages_to_print)
                    except NoPagesToPrintException:
                        _no_pages_cancel(job)
                    handle_cancellation(job)

                    output_file = imposition_template.create_output_pdf(final_pages_file, final_page_processor.final_page_orientation)

                    shutil.copyfile(output_file, os.path.join(job_tmpdir, f'{idx:03}_output.pdf'))
                    sum_num_pages += 1 # TODO: Fix
                    handle_cancellation(job)
            job.status = JobStatus.PRINTING
            job.status_reason = ''
            job.date_processed = timezone.now()
            job.pages = sum_num_pages * job.properties.copies
            job.save()
            backend = {
                PrinterType.DISABLED: DisabledPrinter,
                PrinterType.LOCAL_CUPS: LocalCupsPrinter,
            }.get(job.printer.printer_type, DisabledPrinter)()
            for out in os.listdir(job_tmpdir):
                backend.print(job, os.path.join(job_tmpdir, out))
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
    stale_jobs = GutenbergJob.objects.exclude(status__in=GutenbergJob.COMPLETED_STATUSES).annotate(
        last_activity=Greatest('date_created', Coalesce('date_processed', 0), Coalesce(0, 'date_finished'))).filter(
        last_activity__lt=timezone.now() - datetime.timedelta(seconds=2 * TASK_TIMEOUT_S))
    stale_jobs.update(status=JobStatus.ERROR,
                      status_reason='This task has expired. There is most likely an issue with Gutenberg background '
                                    'workers. Please notify administrators about this.')
