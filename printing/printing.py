# Original script by zielmicha (https://github.com/zielmicha)

import os
import shutil
import subprocess
import tempfile

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from control.models import PrintJob, PrintingProperties, TwoSidedPrinting, JobStatus
from printing.converter import auto_convert
from printing.postprocess import auto_postprocess


def generate_hp500_options(properties: PrintingProperties):
    options = []
    options += ['-n', str(properties.copies)]
    options += ['-o', 'HPColorAsGray={}'.format(not properties.color)]

    two_sided_opt = {
        TwoSidedPrinting.ONE_SIDED: 'None',
        TwoSidedPrinting.TWO_SIDED_LONG_EDGE: 'DuplexNoTumble',
        TwoSidedPrinting.TWO_SIDED_SHORT_EDGE: 'DuplexTumble',
    }[properties.two_sides]
    options += ['-o', 'Duplex={}'.format(two_sided_opt)]
    options += ['-o', 'fit-to-page']
    return options


generate_options = generate_hp500_options


@shared_task
def print_file(file_path, file_format, job_id):
    job = PrintJob.objects.get(id=job_id)
    job.status = JobStatus.PROCESSING
    job.save()
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp()
        ext = file_path.lower().rsplit('.', 1)[-1]
        tmp_input = os.path.join(tmpdir, 'input.' + ext)
        shutil.copyfile(file_path, os.path.join(tmpdir, 'input.' + ext))
        out, out_type = auto_convert(tmp_input, file_format, tmpdir)
        out, num_pages = auto_postprocess(out, out_type, tmpdir, job.properties)
        job.status = JobStatus.PRINTING
        job.date_processed = timezone.now()
        job.pages = num_pages * job.properties.copies
        job.save()
        subprocess.check_call(
            ['lp', out] + ['-d', settings.PRINTER_NAME] +
            generate_options(job.properties))
        shutil.rmtree(tmpdir)
        job.status = JobStatus.COMPLETED
        job.finished = timezone.now()
        job.save()
    except Exception as ex:
        job.status = JobStatus.ERROR
        job.status_reason = repr(ex)[:1999]
        job.save()
        if tmpdir:
            shutil.rmtree(tmpdir)
        raise ex
