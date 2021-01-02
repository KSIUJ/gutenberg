import logging
import os
from datetime import datetime
from secrets import token_urlsafe

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.staticfiles.views import serve
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.views.generic import FormView

from control.models import PrintJob, JobStatus, PrintingProperties, Printer, PrinterPermissions, PrinterPermissionsEnum, \
    TwoSidedPrinting
from printing.converter import detect_file_format, SUPPORTED_FILE_FORMATS
from printing.forms import PrintForm
from printing.printing import print_file

# Time for a session to expire: 30 days
SESSION_EXPIRY = 60 * 60 * 24 * 30

# "Color print" form field name
COLOR_ENABLED_FIELD_NAME = 'color_enabled'
# Whether or not user has recently used color printing
COLOR_ENABLED_SESSION_KEY = 'color_last_enabled'
PRINTER_FIELD_NAME = 'printer'
PRINTER_SESSION_KEY = 'printer_last'

logger = logging.getLogger('gutenberg.printing')


class PrintView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'printing/print.html'
    form_class = PrintForm
    success_url = reverse_lazy('print')
    success_message = 'The document was sent to the printer!'

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        form = form_class(Printer.objects, **self.get_form_kwargs())

        return form

    def get_initial(self):
        initial = super(PrintView, self).get_initial()
        initial[COLOR_ENABLED_FIELD_NAME] = self.request.session.get(
            COLOR_ENABLED_SESSION_KEY, False)
        initial[PRINTER_FIELD_NAME] = self.request.session.get(PRINTER_SESSION_KEY, Printer.objects.first())
        return initial

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        # If the user does not have permission to use color printing,
        # ensure the document will not print with colors
        printer = form.cleaned_data[PRINTER_FIELD_NAME]
        perms = PrinterPermissions.get_permissions(self.request.user, printer)
        if PrinterPermissionsEnum.PRINT not in perms:
            return HttpResponse("Forbidden", status=403, content_type='text/plain')

        if not printer.duplex_supported:
            form.cleaned_data['two_sided'] = TwoSidedPrinting.ONE_SIDED

        if PrinterPermissionsEnum.PRINT_COLOR not in perms or not printer.color_supported:
            form.cleaned_data[COLOR_ENABLED_FIELD_NAME] = False

        # Save last settings in session (except for duplex printing - default to saving paper).
        self.request.session[COLOR_ENABLED_SESSION_KEY] = (
            form.cleaned_data.get(COLOR_ENABLED_FIELD_NAME, False))
        self.request.session.set_expiry(SESSION_EXPIRY)
        self.request.session[PRINTER_SESSION_KEY] = (
            form.cleaned_data.get(PRINTER_FIELD_NAME, None))

        self.upload_and_print_file(**form.cleaned_data)

        return super(PrintView, self).form_valid(form)

    def upload_and_print_file(self, printer, file_to_print: UploadedFile,
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
        file_type = detect_file_format(file_path)
        if file_type not in SUPPORTED_FILE_FORMATS:
            raise ValueError("Unsupported file type")
        job = PrintJob.objects.create(name=file_to_print.name, status=JobStatus.PENDING, owner=self.request.user,
                                      printer=printer)
        PrintingProperties.objects.create(color=color_enabled, copies=copy_number, two_sides=two_sided,
                                          pages_to_print=pages_to_print, job=job)

        print_file.delay(file_path, file_type, job.id)

        logger.info('User %s printed file: "%s" (sudo printing: %s)',
                    self.request.user.username, file_path, color_enabled)


@login_required
def ipp_info(request, printer_id):
    if not request.user.api_key:
        request.user.api_key = token_urlsafe(32)
        request.user.save()
    printer = get_object_or_404(Printer, pk=printer_id)
    host = request.META['HTTP_HOST']
    base_url = ''.join(['ipps' if request.is_secure() else 'ipp', '://', host])
    if ':' not in host:
        base_url += ':443' if request.is_secure() else ':80'
    ipp_url = base_url + reverse('ipp_endpoint', args=['basic', printer_id, 'print'])
    ipp_tokenised_url = base_url + reverse('ipp_endpoint', args=[request.user.api_key, printer_id, 'print'])
    return render(request, 'printing/ipp_info.html', {
        'ipp_tokenised_url': ipp_tokenised_url, 'ipp_url': ipp_url, 'printer': printer,
    })


@login_required
def webapp(request):
    return serve(request, "index.html")
