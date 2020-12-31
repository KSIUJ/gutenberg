import logging
import os
import string

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.forms.utils import ErrorList

from control.models import TwoSidedPrinting
from printing.converter import SUPPORTED_EXTENSIONS

PAGES_REGEX = r"^\s*\d+(?:\s*-\s*\d+)?(\s*,\s*\d+(?:\s*-\s*\d+)?)*\s*$"

logger = logging.getLogger('gutenberg.printing')


class PrintForm(forms.Form):

    def __init__(self, printer_queryset, data=None, files=None, auto_id='id_%s', prefix=None, initial=None,
                 error_class=ErrorList, label_suffix=None, empty_permitted=False, field_order=None,
                 use_required_attribute=None, renderer=None):
        super().__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, field_order,
                         use_required_attribute, renderer)
        self.fields['printer'].queryset = printer_queryset

    printer = forms.ModelChoiceField(
        required=True, queryset=None,
        initial=None, empty_label=None,
    )
    file_to_print = forms.FileField(
        required=True,
        help_text='Supported formats: {}'.format(
            ', '.join(sorted(SUPPORTED_EXTENSIONS))))

    copy_number = forms.IntegerField(label='Copies', initial=1, required=True,
                                     min_value=1, max_value=100)
    pages_to_print = forms.RegexField(
        regex=PAGES_REGEX, label='Pages', max_length=200, required=False,
        help_text='Pages to print, e.g. 1-4, 7, 13-21',
        widget=forms.TextInput(attrs={
            'placeholder': 'All pages',
            'pattern': PAGES_REGEX
        }))
    two_sided = forms.ChoiceField(
        label='Two-sided', choices=TwoSidedPrinting.choices,
        initial=TwoSidedPrinting.TWO_SIDED_LONG_EDGE,
        help_text='Please consider the environment before disabling this '
                  'setting')
    color_enabled = forms.BooleanField(
        label='Enable color (sudo printing)', required=False,
        help_text='Requires being a superuser')

    def clean_file_to_print(self):
        file_to_print: UploadedFile = self.cleaned_data['file_to_print']
        name, ext = os.path.splitext(file_to_print.name)
        ext = ext.replace('.', '')
        if ext.lower() not in SUPPORTED_EXTENSIONS:
            raise ValidationError(
                'Unsupported file format: %(ext)s', code='unsupported_format',
                params={'ext': ext})

        return file_to_print

    def clean_pages_to_print(self):
        pages: str = self.cleaned_data['pages_to_print']
        # Remove all whitespace
        pages = pages.translate(str.maketrans('', '', string.whitespace))
        if pages:
            # Check for invalid page ranges (e.g. 3-1)
            parts = [part.split('-') for part in pages.split(',')]
            for part in parts:
                # In case of single page numbers, part[0] and part[-1] is the
                # same thing, so we don't have to separately check for that
                if int(part[0]) > int(part[-1]):
                    raise ValidationError('Invalid page range: {}-{}'
                                          .format(part[0], part[-1]))

        return pages
