from django import forms

from control.models import LocalPrinterParams
from control.widgets import CupsPrinterNameAutocomplete
from printing.backends import LocalCupsPrinter


class LocalPrinterParamsForm(forms.ModelForm):
    class Meta:
        model = LocalPrinterParams
        fields = '__all__'
        widgets = {
            'cups_printer_name': CupsPrinterNameAutocomplete(
                get_printer_names=LocalCupsPrinter.list_cups_printer_names
            )
        }
