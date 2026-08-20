from django import forms
from django.urls import reverse


class CupsPrinterNameAutocomplete(forms.TextInput):
    template_name = "widgets/cups_printer_name_autocomplete.html"

    def __init__(self, attrs=None, get_printer_names=None):
        super().__init__(attrs)
        self.get_printer_names = get_printer_names or (lambda: [])

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        printer_names = self.get_printer_names()
        context["printer_names"] = printer_names
        context["cups_printer_options_url"] = reverse('admin:control_printer_cups_printer_options')
        return context

    class Media:
        js = ("js/cups_printer_name_autocomplete.js",)
        css = {"all": ("css/cups_printer_name_autocomplete.css",)}
