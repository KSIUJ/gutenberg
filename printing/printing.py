import os
import shutil
import subprocess
import tempfile

from celery import shared_task
from django.utils import timezone

from control.models import PrintJob, TwoSidedPrinting, JobStatus, PrinterType
from printing.converter import auto_convert
from printing.postprocess import auto_postprocess


def print_local_cups(file_path: str, job: PrintJob):
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

    subprocess.check_call(
        ['lp', file_path] + options)
    job.status = JobStatus.COMPLETED
    job.finished = timezone.now()
    job.save()


def print_disabled(file_path: str, job: PrintJob):
    job.status = JobStatus.CANCELED
    job.status_reason = "Printer is disabled"
    job.finished = timezone.now()
    job.save()


@shared_task
def print_file(file_path, file_format, job_id):
    job = PrintJob.objects.get(id=job_id)
    job.status = JobStatus.PROCESSING
    job.save()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            ext = file_path.lower().rsplit('.', 1)[-1]
            tmp_input = os.path.join(tmpdir, 'input.' + ext)
            shutil.copyfile(file_path, os.path.join(tmpdir, 'input.' + ext))
            out, out_type = auto_convert(tmp_input, file_format, tmpdir)
            out, num_pages = auto_postprocess(out, out_type, tmpdir, job.properties)
            job.status = JobStatus.PRINTING
            job.date_processed = timezone.now()
            job.pages = num_pages * job.properties.copies
            job.save()
            {
                PrinterType.DISABLED: print_disabled,
                PrinterType.LOCAL_CUPS: print_local_cups,
            }.get(job.printer.printer_type, PrinterType.DISABLED)(out, job)
    except Exception as ex:
        job.status = JobStatus.ERROR
        job.status_reason = repr(ex)
        job.save()
        raise ex
