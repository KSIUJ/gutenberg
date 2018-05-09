import logging
from datetime import datetime

import os
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import FormView, RedirectView

from printing.forms import PrintForm, LoginForm
from printing.printing import print_file

# Time for a session to expire: 30 days
SESSION_EXPIRY = 60 * 60 * 24 * 30

# Session/form keys
USERNAME_SESSION_KEY = 'user'
# Whether or not user is allowed to color print
USER_COLOR_ENABLED_SESSION_KEY = 'user_color_enabled'
# "Color print" form field name
COLOR_ENABLED_FIELD_NAME = 'color_enabled'
# Whether or not user has recently used color printing
COLOR_ENABLED_SESSION_KEY = 'color_last_enabled'

logger = logging.getLogger('gutenberg.printing')


class LoginRequiredMixin:
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if (USERNAME_SESSION_KEY not in request.session or
                USER_COLOR_ENABLED_SESSION_KEY not in request.session):
            return HttpResponseRedirect(reverse('login'))
        return super(LoginRequiredMixin, self).dispatch(
            request, *args, **kwargs)


class PrintView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = 'printing/print.html'
    form_class = PrintForm
    success_url = reverse_lazy('print')
    success_message = 'The document was sent to the printer!'

    def get_form(self, form_class=None):
        form = super(PrintView, self).get_form(form_class)
        if not self.request.session[USER_COLOR_ENABLED_SESSION_KEY]:
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

        # If the user does not have permission to use color printing,
        # ensure the document will not print with colors
        if not self.request.session[USER_COLOR_ENABLED_SESSION_KEY]:
            form.cleaned_data[COLOR_ENABLED_FIELD_NAME] = False

        self.upload_and_print_file(username=self.request.session['user'],
                                   **form.cleaned_data)

        return super(PrintView, self).form_valid(form)

    @staticmethod
    def upload_and_print_file(file_to_print: UploadedFile, username: str,
                              copy_number: int, pages_to_print: str,
                              color_enabled: bool, two_sided_enabled: bool,
                              **_):
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


class LoginView(FormView):
    template_name = 'printing/login.html'
    form_class = LoginForm
    success_url = reverse_lazy('print')

    def form_valid(self, form):
        # "color_enabled" form field is added by our clean() method
        self.login_user(form.cleaned_data['username'],
                        form.cleaned_data['color_enabled'])
        return super(LoginView, self).form_valid(form)

    def login_user(self, username: str, color_enabled: bool):
        self.request.session[USERNAME_SESSION_KEY] = username
        self.request.session[USER_COLOR_ENABLED_SESSION_KEY] = color_enabled
        self.request.session.set_expiry(SESSION_EXPIRY)


class LogoutView(LoginRequiredMixin, RedirectView):
    pattern_name = 'login'

    def get_redirect_url(self, *args, **kwargs):
        messages.info(self.request, 'You were signed out.')
        self.logout_user()

        return super(LogoutView, self).get_redirect_url(*args, **kwargs)

    def logout_user(self):
        del self.request.session[USERNAME_SESSION_KEY]
        del self.request.session[USER_COLOR_ENABLED_SESSION_KEY]
