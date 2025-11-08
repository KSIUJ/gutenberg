# The filename of this file is important
# `app.autodiscover_tasks()` will look for the commands in the `tasks` module of each registered Django app.

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
