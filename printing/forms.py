import logging
import string

import os
import pam
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from printing.printing import SUPPORTED_FILE_FORMATS

PAGES_REGEX = r"^\s*\d+(?:\s*-\s*\d+)?(\s*,\s*\d+(?:\s*-\s*\d+)?)*\s*$"

logger = logging.getLogger('gutenberg.printing')


class PrintForm(forms.Form):
    file_to_print = forms.FileField(
        required=True,
        help_text='Supported formats: {}'.format(
            ', '.join(SUPPORTED_FILE_FORMATS)))

    copy_number = forms.IntegerField(label='Copies', initial=1, required=True,
                                     min_value=1, max_value=100)
    pages_to_print = forms.RegexField(
        regex=PAGES_REGEX, label='Pages', max_length=200, required=False,
        help_text='Pages to print, e.g. 1-4, 7, 13-21',
        widget=forms.TextInput(attrs={
            'placeholder': 'All pages',
            'pattern': PAGES_REGEX
        }))
    two_sided_enabled = forms.BooleanField(
        label='Two-sided', initial=True, required=False,
        help_text='Please consider the environment before disabling this '
                  'setting')
    color_enabled = forms.BooleanField(
        label='Enable color (sudo printing)', required=False,
        help_text='Requires being a superuser')

    def clean_file_to_print(self):
        file_to_print: UploadedFile = self.cleaned_data['file_to_print']
        name, ext = os.path.splitext(file_to_print.name)
        ext = ext.replace('.', '')
        if ext.lower() not in SUPPORTED_FILE_FORMATS:
            raise ValidationError(
                'Unsupported file format: %(ext)s', code='unsupported_format',
                params={'ext': ext})

        return file_to_print

    def clean_pages_to_print(self):
        pages_to_print: str = self.cleaned_data['pages_to_print']
        # Remove all whitespace
        return pages_to_print.translate(
            str.maketrans('', '', string.whitespace))


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
