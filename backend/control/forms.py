import logging

from celery.app.control import flatten_reply
from django import forms

from control.models import LocalPrinterParams
from control.widgets import CupsPrinterNameAutocomplete
from gutenberg.celery import app

logger = logging.getLogger('gutenberg.control')


def _get_printer_names():
    # `limit=1` will lead to race conditions if multiple workers are running, and they have access to different printers.
    # If the param was not used, the worker would always wait for the duration specified in `timeout`, even if all the
    # workers have already responded.
    try:
        replies = app.control.broadcast("gutenberg_list_cups_printer_names", reply=True, limit=1, timeout=1)
        replies = [reply for reply in flatten_reply(replies).values() if "error" not in reply]
        if len(replies) == 0:
            return []
        return replies[0]
    except Exception:
        logger.exception("Failed to get printer names from workers", exc_info=True)
        return []


class LocalPrinterParamsForm(forms.ModelForm):
    class Meta:
        model = LocalPrinterParams
        fields = '__all__'
        widgets = {
            'cups_printer_name': CupsPrinterNameAutocomplete(
                get_printer_names=_get_printer_names
            )
        }
