# Original script by zielmicha (https://github.com/zielmicha)

import shutil
import subprocess
import tempfile

import os

from celery import shared_task
from django.conf import settings

from control.models import PrintJob, PrintingProperties, TwoSidedPrinting, JobStatus
from printing.converter import auto_convert

DOCUMENT_FORMATS = ('doc', 'docx', 'rtf', 'odt')
IMAGE_FORMATS = ('png', 'jpg', 'jpeg')
PDF_FORMAT = ('pdf',)
SUPPORTED_FILE_FORMATS = DOCUMENT_FORMATS + IMAGE_FORMATS + PDF_FORMAT

TWO_SIDED_DISABLED = 'None'
TWO_SIDED_LONG_EDGE = 'LongEdge'
TWO_SIDED_SHORT_EDGE = 'ShortEdge'


def generate_hp500_options(properties: PrintingProperties):
    options = []
    options += ['-n', str(properties.copies)]
    if properties.pages_to_print:
        options += ['-P', properties.pages_to_print]
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
def print_file(file_path, job_id):
    job = PrintJob.objects.get(id=job_id)
    job.status = JobStatus.PROCESSING
    job.save()
    try:
        tmpdir = tempfile.mkdtemp()
        ext = file_path.lower().rsplit('.', 1)[-1]
        tmp_input = os.path.join(tmpdir, 'input.' + ext)
        shutil.copyfile(file_path, os.path.join(tmpdir, 'input.' + ext))
        out = auto_convert(tmp_input, 'gutenberg/pdf', tmpdir)
        job.status = JobStatus.PRINTING
        job.save()
        subprocess.check_call(
            ['lp', out] + ['-d', settings.PRINTER_NAME] +
            generate_options(job.properties))
        shutil.rmtree(tmpdir)
        job.status = JobStatus.COMPLETED
        job.save()
    except Exception as ex:
        job.status = JobStatus.ERROR
        job.status_reason = repr(ex)[:1999]
        job.save()
        raise ex
