import logging
from celery.app.control import flatten_reply
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotAllowed, JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from control.forms import LocalPrinterParamsForm
from control.models import (
    GutenbergJob,
    GroupQuota,
    JobArtefact,
    LocalPrinterParams,
    Printer,
    PrinterPermissions,
    PrintingProperties,
)
from control.views import trigger_test_print_view
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
        label='Daily page limit',
        required=False,
        min_value=0,
        help_text='Maximum printed pages per day. Leave blank for no group quota; 0 means unlimited.',
    )
    weekly_limit = forms.IntegerField(
        label='Weekly page limit',
        required=False,
        min_value=0,
        help_text='Maximum printed pages per week. Leave blank for no group quota; 0 means unlimited.',
    )
    monthly_limit = forms.IntegerField(
        label='Monthly page limit',
        required=False,
        min_value=0,
        help_text='Maximum printed pages per month. Leave blank for no group quota; 0 means unlimited.',
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
    list_display = ('name', 'availability', 'display_order', 'test_print_controls')
    list_filter = ('availability',)
    ordering = ('display_order', 'name')
    readonly_fields = ('test_print_controls',)

    def get_urls(self):
        """Returns HTML for Django admin list view"""
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:printer_id>/test-print/',
                self.admin_site.admin_view(trigger_test_print_view),
                name='control_printer_test_print',
            ),
            path(
                'cups-printer-options/',
                self.admin_site.admin_view(self.cups_printer_options_view),
                name='control_printer_cups_printer_options',
            ),
        ]
        return custom_urls + urls

    def test_print_controls(self, obj):
        """
        Renders action buttons for test prints in different configurations (one-sided/two-sided, colored/grayscale).
        """
        if not obj or not obj.pk:
            return "-"

        url = reverse('admin:control_printer_test_print', args=[obj.pk])

        test_variants = [
            ('Grayscale one-sided', False, False, 'btn-grayscale-one-sided'),
            ('Colored one-sided', True, False, 'btn-colored-one-sided'),
            ('Grayscale two-sided', False, True, 'btn-grayscale-two-sided'),
            ('Colored two-sided', True, True, 'btn-colored-two-sided'),
        ]

        buttons_html = '<div style="display: flex; gap: 8px; flex-wrap: wrap;">'

        for label, color, duplex, css_class in test_variants:
            btn_html = (
                f'<button type="button" class="admin-test-print-btn {css_class}" '
                f'data-url="{url}" data-color="{str(color).lower()}" data-duplex="{str(duplex).lower()}" '
                f'style="padding: 8px 12px; font-size: 12px; font-weight: bold; '
                f'border: none; border-radius: 4px; cursor: pointer; '
                f'background-color: #417690; color: white; transition: all 0.2s;" '
                f'onmouseover="this.style.backgroundColor=\'#2a4d63\';" '
                f'onmouseout="this.style.backgroundColor=\'#417690\';">'
                f'{label}'
                f'</button>'
            )
            buttons_html += btn_html

        buttons_html += '</div>'

        return mark_safe(buttons_html)

    test_print_controls.short_description = 'Test Print Options'

    class Media:
        """Class for loading js script"""
        js = ('js/admin_test_print.js',)

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
