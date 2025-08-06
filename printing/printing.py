import datetime
import logging
import os
import shutil
import tempfile
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db.models.functions import Greatest, Coalesce
from django.utils import timezone
from django.db.models import DateTimeField, Value, F

from control.models import GutenbergJob, TwoSidedPrinting, JobStatus, PrinterType, Printer, PrintingProperties, \
    JobArtefact, JobArtefactType
from printing.backends import DisabledPrinter, LocalCupsPrinter
from printing.converter import auto_convert, detect_file_format
from printing.postprocess import auto_postprocess
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
        with tempfile.TemporaryDirectory() as job_tmpdir:
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
                    out, out_type = auto_convert(tmp_input, file_format, artefact_tmpdir)
                    handle_cancellation(job)
                    out, num_pages = auto_postprocess(out, out_type, artefact_tmpdir, job)
                    shutil.copyfile(out, os.path.join(job_tmpdir, f'{idx:03}_{os.path.basename(out)}'))
                    sum_num_pages += num_pages
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
    stale_jobs = GutenbergJob.objects.exclude(
        status__in=GutenbergJob.COMPLETED_STATUSES
    ).annotate(
        created_coalesced=Coalesce('date_created', Value(datetime.datetime.min, output_field=DateTimeField())),
        processed_coalesced=Coalesce('date_processed', Value(datetime.datetime.min, output_field=DateTimeField())),
        finished_coalesced=Coalesce('date_finished', Value(datetime.datetime.min, output_field=DateTimeField())),
    ).annotate(
        last_activity=Greatest(
            F('created_coalesced'),
            F('processed_coalesced'),
            F('finished_coalesced'),
            output_field=DateTimeField()
        )
    ).filter(
        last_activity__lt=timezone.now() - datetime.timedelta(seconds=2 * TASK_TIMEOUT_S)
    )

    for job in stale_jobs:
        backend = {
            PrinterType.DISABLED: DisabledPrinter,
            PrinterType.LOCAL_CUPS: LocalCupsPrinter,
        }.get(job.printer.printer_type, DisabledPrinter)()
        backend_job_id = getattr(job, 'backend_job_id', None)
        if backend_job_id and backend.check_status(job, backend_job_id):
            continue
        try:
            backend.cancel_job(job, backend_job_id)
        except Exception as ex:
            logger.warning(f"Could not cancel job {job.id} in backend: {ex}")
        job.status = JobStatus.ERROR
        job.status_reason = (
            'This task has expired and was canceled in backend. '
            'There is most likely an issue with Gutenberg background workers. '
            'Please notify administrators about this.'
        )
        job.save()
