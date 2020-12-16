import logging
import os
from datetime import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import FormView

from control.models import PrintJob, JobStatus, PrintingProperties, TwoSidedPrinting
from printing.forms import PrintForm
from printing.printing import print_file, TWO_SIDED_DISABLED, TWO_SIDED_LONG_EDGE, TWO_SIDED_SHORT_EDGE

# Time for a session to expire: 30 days
SESSION_EXPIRY = 60 * 60 * 24 * 30

# "Color print" form field name
COLOR_ENABLED_FIELD_NAME = 'color_enabled'
# Whether or not user has recently used color printing
COLOR_ENABLED_SESSION_KEY = 'color_last_enabled'

logger = logging.getLogger('gutenberg.printing')


class PrintView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'printing/print.html'
    form_class = PrintForm
    success_url = reverse_lazy('print')
    success_message = 'The document was sent to the printer!'

    def get_form(self, form_class=None):
        form = super(PrintView, self).get_form(form_class)
        if not self.request.user.can_color_print:
            form.fields.pop(COLOR_ENABLED_FIELD_NAME)
        return form

    def get_initial(self):
        initial = super(PrintView, self).get_initial()
        initial[COLOR_ENABLED_FIELD_NAME] = self.request.session.get(
            COLOR_ENABLED_SESSION_KEY, False)
        return initial

    def form_valid(self, form):
        # Save "last color enabled" value in session
        self.request.session[COLOR_ENABLED_SESSION_KEY] = (
            form.cleaned_data.get(COLOR_ENABLED_FIELD_NAME, False))
        self.request.session.set_expiry(SESSION_EXPIRY)

        # If the user does not have permission to use color printing,
        # ensure the document will not print with colors
        if not self.request.user.can_color_print:
            form.cleaned_data[COLOR_ENABLED_FIELD_NAME] = False

        self.upload_and_print_file(**form.cleaned_data)

        return super(PrintView, self).form_valid(form)

    def upload_and_print_file(self, file_to_print: UploadedFile,
                              copy_number: int, pages_to_print: str,
                              color_enabled: bool, two_sided: str, **_):
        name, ext = os.path.splitext(file_to_print.name)
        name = slugify(name)
        file_name = '{}_{}_{}'.format(
            name, self.request.user.username,
            datetime.now().strftime(settings.PRINT_DATE_FORMAT))
        file_path = os.path.join(settings.PRINT_DIRECTORY, file_name + ext)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb+') as destination:
            for chunk in file_to_print.chunks():
                destination.write(chunk)

        ts = {
            TWO_SIDED_DISABLED: TwoSidedPrinting.ONE_SIDED,
            TWO_SIDED_LONG_EDGE: TwoSidedPrinting.TWO_SIDED_LONG_EDGE,
            TWO_SIDED_SHORT_EDGE: TwoSidedPrinting.TWO_SIDED_SHORT_EDGE,
        }.get(two_sided, TwoSidedPrinting.TWO_SIDED_LONG_EDGE)
        job = PrintJob.objects.create(name=file_to_print.name, status=JobStatus.PENDING, owner=self.request.user)
        PrintingProperties.objects.create(color=color_enabled, copies=copy_number, two_sides=ts,
                                          pages_to_print=pages_to_print, job=job)

        print_file.delay(file_path, job.id)

        logger.info('User %s printed file: "%s" (sudo printing: %s)',
                    self.request.user.username, file_path, color_enabled)
