# The filename of this file is important
# `app.autodiscover_tasks()` will look for the commands in the `tasks` module of each registered Django app.

import os
import shutil
import subprocess
from celery import shared_task
from django.conf import settings
from django.utils import timezone

import logging
from itertools import chain

from celery.worker.control import control_command

from printing.backends import LocalCupsPrinter
from printing.processing.converter import CONVERTERS_LOCAL

logger = logging.getLogger('gutenberg.worker')


@control_command(name="gutenberg_get_supported_formats")
def get_own_supported_formats(state) -> dict:
    """
    A Celery command to get the document formats supported by the current worker.
    `get_formats_supported_by_workers` uses this command.
    """

    return {
        "mime_types": list(chain.from_iterable(conv.supported_types for conv in CONVERTERS_LOCAL)),
        "extensions": list(chain.from_iterable(conv.supported_extensions for conv in CONVERTERS_LOCAL)),
    }


@control_command(name="gutenberg_list_cups_printer_names")
def list_cups_printer_names(state) -> list[str]:
    return LocalCupsPrinter.list_cups_printer_names()

@shared_task(bind=True, max_retries=2)
def generate_preview(self, printjob_id: int, max_pages: int = 5, dpi: int = 150):
    """
    Konwertuje uploaded_file -> pdf (jeśli trzeba) -> PNG pierwszych max_pages stron.
    Zapisuje pliki w MEDIA_ROOT/previews/{printjob_id}/page-1.png ...
    Aktualizuje pola PrintJob.preview_status / preview_pages / preview_meta.
    """
    try:
        pj = PrintJob.objects.get(pk=printjob_id)
    except PrintJob.DoesNotExist:
        return

    pj.preview_status = PrintJob.PREVIEW_PROCESSING
    pj.save(update_fields=['preview_status'])

    media_root = settings.MEDIA_ROOT
    tmpdir = os.path.join(media_root, 'previews_tmp', str(pj.id))
    outdir = os.path.join(media_root, pj.preview_dir())
    os.makedirs(tmpdir, exist_ok=True)
    os.makedirs(outdir, exist_ok=True)

    try:
        input_path = pj.uploaded_file.path

        # 1) jeżeli nie PDF, konwertuj do PDF przez LibreOffice (soffice)
        if not input_path.lower().endswith('.pdf'):
            subprocess.check_call([
                'soffice', '--headless', '--invisible', '--convert-to', 'pdf', '--outdir', tmpdir, input_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # znajdź pierwszy pdf w tmpdir
            pdfs = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.lower().endswith('.pdf')]
            if not pdfs:
                raise RuntimeError("LibreOffice conversion failed")
            pdf_path = pdfs[0]
        else:
            pdf_path = input_path

        # 2) rasteryzacja do PNG (pdftoppm)
        prefix = os.path.join(outdir, 'page')
        subprocess.check_call([
            'pdftoppm', '-png', '-r', str(dpi), '-f', '1', '-l', str(max_pages), pdf_path, prefix
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3) zbierz nazwy plików
        pages = sorted([f for f in os.listdir(outdir) if f.startswith('page') and f.endswith('.png')])
        pj.preview_pages = len(pages)
        pj.preview_meta = {'pages': pages}
        pj.preview_status = PrintJob.PREVIEW_READY
        pj.save(update_fields=['preview_pages', 'preview_meta', 'preview_status'])
    except Exception as exc:
        pj.preview_status = PrintJob.PREVIEW_FAILED
        pj.save(update_fields=['preview_status'])
        # retry jeśli potrzeba
        try:
            raise self.retry(exc=exc, countdown=5)
        except Exception:
            # nie udało się zretryować
            pass
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
