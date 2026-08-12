import os
import logging
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.contrib.staticfiles.finders import find
from django.core.files import File
from celery import current_app

from control.models import (
    GutenbergJob,
    PrintingProperties,
    JobArtefact,
    Printer,
    JobType,
    JobStatus,
    JobArtefactType,
    TwoSidedPrinting,
    PrintPreview,
    PreviewStatus,
    PrinterType,
)
from printing.printing import print_file

logger = logging.getLogger('gutenberg.printing.services')


def validate_properties(user, printer_id: int, properties, job=None):
    """
    Validates printing properties for the given user and printer id.
    Raises:
      - ObjectDoesNotExist if printer is not available to user
      - ValidationError for property issues (color/duplex not allowed)
    Returns:
      printer_with_perms (Printer)
    """
    printer_with_perms = Printer.get_printer_for_user(user=user, printer_id=printer_id)
    if not printer_with_perms:
        raise ObjectDoesNotExist("Selected printer does not exist")

    if properties.color and not getattr(printer_with_perms, 'color_allowed', False):
        raise ValidationError("Color printing is not allowed on the selected printer")

    if properties.two_sides != TwoSidedPrinting.ONE_SIDED and not printer_with_perms.duplex_supported:
        raise ValidationError("Two-sided printing is not supported on the selected printer")

    return printer_with_perms


def create_printing_job(user,
                        printer_with_perms: Printer,
                        *,
                        name: str = 'webrequest',
                        copies: int = 1,
                        pages_to_print: str = None,
                        color: bool = False,
                        two_sides: str = TwoSidedPrinting.ONE_SIDED,
                        fit_to_page: bool = True,
                        n_up: int = 1,
                        imposition_template: str = None,
                        orientation_requested: str = None):
    """
    Create GutenbergJob and associated PrintingProperties (job status = INCOMING).
    Returns created job.
    """
    with transaction.atomic():
        job = GutenbergJob(
            name=name,
            job_type=JobType.PRINT,
            status=JobStatus.INCOMING,
            owner=user,
            printer=printer_with_perms,
        )
        # create printing properties instance but do not save until job is saved
        job.properties = PrintingProperties(
            color=color,
            copies=copies,
            two_sides=two_sides,
            pages_to_print=None if pages_to_print == "" else pages_to_print,
            job=job,
            fit_to_page=fit_to_page,
            n_up=n_up,
            imposition_template=imposition_template or PrintingProperties._meta.get_field('imposition_template').get_default(),
            orientation_requested=orientation_requested or PrintingProperties._meta.get_field('orientation_requested').get_default(),
        )

        # run shared validation
        validate_properties(user=user, printer_id=printer_with_perms.id, properties=job.properties, job=job)

        job.save()
        job.properties.save()
        return job


def run_job(job, request_user=None):
    """
    Start job using the same logic as API._run_job:
     - cancel pending preview task if needed,
     - set job.status = PENDING
     - enqueue print_file.delay(job.id)
    """
    try:
        preview = job.preview
    except PrintPreview.DoesNotExist:
        preview = None

    if preview is not None:
        if preview.status in (PreviewStatus.PENDING, PreviewStatus.PROCESSING):
            if preview.celery_task_id:
                try:
                    current_app.control.revoke(preview.celery_task_id, terminate=False)
                except Exception:
                    logger.exception("Failed to revoke previous preview task %s", preview.celery_task_id)
            preview.status = PreviewStatus.CANCELED
            preview.save(update_fields=['status', 'updated_at'])

    job.status = JobStatus.PENDING
    job.save(update_fields=['status'])
    print_file.delay(job.id)

    if request_user:
        logger.info('User %s submitted job: %s', getattr(request_user, 'username', '<unknown>'), job.id)
    else:
        logger.info('Job submitted (no user): %s', job.id)

    return job


def trigger_test_print_from_file(printer: Printer, user, file_path: str, *, color: bool = False, duplex: bool = False):
    """
    Creates and enqueues a test print job for the given printer using a PDF file.
    Returns the created job.
    """
    # Validate printer type (accept model enum or string)
    if getattr(printer, 'printer_type', None) not in (PrinterType.LOCAL_CUPS, 'LP',):
        raise ValidationError("Test print is only supported for local CUPS printers (type LP).")

    if color and not printer.color_supported:
        raise ValidationError(f"Printer '{printer.name}' does not support color printing.")
    if duplex and not printer.duplex_supported:
        raise ValidationError(f"Printer '{printer.name}' does not support duplex printing.")

    if not os.path.exists(file_path):
        raise ValidationError(f"Test document not found: {file_path}")

    two_sided_option = TwoSidedPrinting.TWO_SIDED_LONG_EDGE if duplex else TwoSidedPrinting.ONE_SIDED

    # create job (uses shared validation)
    job = create_printing_job(
        user=user,
        printer_with_perms=printer,
        name=f"Admin Test Print - {printer.name}",
        copies=1,
        pages_to_print=None,
        color=color,
        two_sides=two_sided_option,
        fit_to_page=True,
        n_up=1,
    )

    # attach artefact
    with open(file_path, 'rb') as f:
        JobArtefact.objects.create(
            job=job,
            file=File(f, name=os.path.basename(file_path)),
            artefact_type=JobArtefactType.SOURCE,
            mime_type='application/pdf',
            document_number=1,
        )

    # run via shared runner (sets PENDING + enqueue)
    run_job(job, request_user=user)
    return job


def find_test_pdf_from_static(relative_static_path='documents/test_page.pdf'):
    """
    Uses staticfiles finder to locate the PDF. Returns absolute path or None.
    """
    path = find(relative_static_path)
    return path
