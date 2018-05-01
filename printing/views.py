import logging
import os
from datetime import datetime

from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse_lazy
from django.views.generic import FormView

from printing.forms import PrintForm
from printing.printing import print_file

logger = logging.getLogger('gutenberg.printing')


def upload_and_print_file(file_to_print: UploadedFile, username: str,
                          copy_number: int, pages_to_print: str,
                          color_enabled: bool, two_sided_enabled: bool, **_):
    name, ext = os.path.splitext(file_to_print.name)
    file_name = '{}_{}_{}'.format(
        name, username,
        datetime.now().strftime(settings.PRINT_DATE_FORMAT))
    file_path = os.path.join(settings.PRINT_DIRECTORY, file_name + ext)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb+') as destination:
        for chunk in file_to_print.chunks():
            destination.write(chunk)

    print_file(
        file_path, copy_number=copy_number, pages_to_print=pages_to_print,
        color_enabled=color_enabled, two_sided_enabled=two_sided_enabled)

    logger.info('User %s printed file: "%s" (sudo printing: %s)',
                username, file_path, color_enabled)


class PrintView(SuccessMessageMixin, FormView):
    COLOR_ENABLED_FIELD_NAME = 'color_enabled'
    COLOR_ENABLED_SESSION_KEY = 'color_enabled'

    template_name = 'printing/print.html'
    form_class = PrintForm
    success_url = reverse_lazy('print')
    success_message = 'The document was sent to the printer!'

    def get_initial(self):
        initial = super(PrintView, self).get_initial()
        initial[self.COLOR_ENABLED_FIELD_NAME] = self.request.session.get(
            self.COLOR_ENABLED_SESSION_KEY, False)
        return initial

    def form_valid(self, form):
        self.request.session[self.COLOR_ENABLED_SESSION_KEY] = (
            form.cleaned_data[self.COLOR_ENABLED_FIELD_NAME])

        upload_and_print_file(**form.cleaned_data)

        return super(PrintView, self).form_valid(form)
