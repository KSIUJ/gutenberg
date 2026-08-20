import logging

from celery.app.control import flatten_reply
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import path

from control.forms import LocalPrinterParamsForm
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, \
    JobArtefact, GroupQuota
from gutenberg.celery import app

logger = logging.getLogger('gutenberg.control')

class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class JobArtefactAdmin(admin.TabularInline):
    model = JobArtefact


class GutenbergJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, JobArtefactAdmin]
    readonly_fields = ('pages', 'date_created', 'date_processed', 'date_finished')
    list_display = ('date_created', 'owner', 'name', 'job_type', 'status', 'pages')
    list_filter = ('date_created', 'owner', 'job_type', 'status')


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams
    form = LocalPrinterParamsForm


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class QuotaGroupAdminForm(forms.ModelForm):
    daily_limit = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='Leave blank for no group limit; 0 means unlimited.',
    )
    weekly_limit = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='Leave blank for no group limit; 0 means unlimited.',
    )
    monthly_limit = forms.IntegerField(
        required=False,
        min_value=0,
        help_text='Leave blank for no group limit; 0 means unlimited.',
    )

    class Meta:
        model = Group
        fields = ('name', 'permissions')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            return
        try:
            quota = self.instance.groupquota
        except GroupQuota.DoesNotExist:
            return
        for field_name in ('daily_limit', 'weekly_limit', 'monthly_limit'):
            self.initial[field_name] = getattr(quota, field_name)


class QuotaGroupAdmin(GroupAdmin):
    form = QuotaGroupAdminForm
    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Permissions', {'fields': ('permissions',)}),
        ('Print quota', {
            'fields': ('daily_limit', 'weekly_limit', 'monthly_limit'),
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        GroupQuota.objects.update_or_create(
            group=obj,
            defaults={
                field_name: form.cleaned_data[field_name]
                for field_name in ('daily_limit', 'weekly_limit', 'monthly_limit')
            },
        )


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]
    list_display = ('name', 'display_order')
    ordering = ('display_order', 'name')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'cups-printer-options/',
                self.admin_site.admin_view(self.cups_printer_options_view),
                name='control_printer_cups_printer_options',
            ),
        ]
        return custom_urls + urls

    def cups_printer_options_view(self, request):
        """Return Gutenberg's supported CUPS settings for a selected queue."""
        if request.method != 'GET':
            return HttpResponseNotAllowed(['GET'])

        if not (self.has_add_permission(request) or self.has_change_permission(request)):
            raise PermissionDenied

        cups_printer_name = request.GET.get('name', '').strip()
        if not cups_printer_name:
            return JsonResponse({'error': 'The "name" query parameter is required.'}, status=400)
        if len(cups_printer_name) > 128:
            return JsonResponse({'error': 'The printer name is too long.'}, status=400)

        try:
            replies = app.control.broadcast(
                'gutenberg_get_cups_printer_options',
                arguments={'cups_printer_name': cups_printer_name},
                reply=True,
                limit=1,
                timeout=5,
            )
            replies = [
                reply for reply in flatten_reply(replies).values()
                if isinstance(reply, dict) and 'error' not in reply
            ]
        except Exception:
            logger.exception('Failed to get CUPS printer options from workers')
            return JsonResponse({'error': 'Could not contact a printing worker.'}, status=503)

        if not replies:
            return JsonResponse({'error': 'No printing worker returned printer capabilities.'}, status=503)
        if not replies[0]:
            return JsonResponse({'error': 'Could not discover capabilities for this printer.'}, status=502)

        return JsonResponse(replies[0])


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
admin.site.unregister(Group)
admin.site.register(Group, QuotaGroupAdmin)
