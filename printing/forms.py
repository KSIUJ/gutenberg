import logging
import os
import string
from typing import List

import pam
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from printing.printing import (
    SUPPORTED_FILE_FORMATS, TWO_SIDED_SHORT_EDGE, TWO_SIDED_LONG_EDGE,
    TWO_SIDED_DISABLED)

PAGES_REGEX = r"^\s*\d+(?:\s*-\s*\d+)?(\s*,\s*\d+(?:\s*-\s*\d+)?)*\s*$"

logger = logging.getLogger('gutenberg.printing')

TWO_SIDED_CHOICES = (
    (TWO_SIDED_DISABLED, 'Disabled'),
    (TWO_SIDED_LONG_EDGE, 'Flip on Long Edge'),
    (TWO_SIDED_SHORT_EDGE, 'Flip on Short Edge'),
)


class PrintForm(forms.Form):
    files_to_print = forms.FileField(
        required=True,
        help_text='Supported formats: {}'.format(
            ', '.join(SUPPORTED_FILE_FORMATS)),
        widget=forms.ClearableFileInput(attrs={'multiple': True}))

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
        label='Two-sided', choices=TWO_SIDED_CHOICES,
        initial=TWO_SIDED_LONG_EDGE,
        help_text='Please consider the environment before disabling this '
                  'setting')
    color_enabled = forms.BooleanField(
        label='Enable color (sudo printing)', required=False,
        help_text='Requires being a superuser')

    def clean_files_to_print(self):
        files_to_print: List[UploadedFile] = self.files.getlist('files_to_print')
        for file in files_to_print:
            name, ext = os.path.splitext(file.name)
            ext = ext.replace('.', '')
            if ext.lower() not in SUPPORTED_FILE_FORMATS:
                raise ValidationError(
                    'Unsupported file format: %(ext)s', code='unsupported_format',
                    params={'ext': ext})

        return files_to_print

    def clean_pages_to_print(self):
        pages: str = self.cleaned_data['pages_to_print']
        # Remove all whitespace
        pages = pages.translate(str.maketrans('', '', string.whitespace))

        # Check for invalid page ranges (e.g. 3-1)
        parts = [part.split('-') for part in pages.split(',')]
        for part in parts:
            # In case of single page numbers, part[0] and part[-1] is the
            # same thing, so we don't have to separately check for that
            if part[0] > part[-1]:
                raise ValidationError('Invalid page range: {}-{}'
                                      .format(part[0], part[-1]))

        return pages


class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=50, required=True)
    password = forms.CharField(label='Password', max_length=200, required=True,
                               widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()

        # Check the credentials
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        color_enabled = True

        if (settings.PRINT_AUTHENTICATE and username and password and
                color_enabled is not None):
            p = pam.pam()

            # Try to authenticate with with color enabled first
            authenticated = p.authenticate(
                username, password, settings.PRINT_COLOR_SERVICE_NAME)
            if not authenticated:
                authenticated = p.authenticate(
                    username, password, settings.PRINT_SERVICE_NAME)
                color_enabled = False

            if not authenticated:
                self.add_error('password',
                               'Could not authenticate: {}'.format(p.reason))
                logger.info(
                    'Could not authenticate user %s: %s (sudo printing: %s)',
                    username, p.reason, color_enabled)

        cleaned_data['color_enabled'] = color_enabled

        return cleaned_data
