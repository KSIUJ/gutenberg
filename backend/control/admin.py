# backend/control/admin.py
from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html

from control.forms import LocalPrinterParamsForm
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, \
    LocalPrinterParams, Printer, JobArtefact
from control.views import trigger_test_print_view


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


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]
    list_display = ('name', 'display_order', 'test_print_button')
    ordering = ('display_order', 'name')
    readonly_fields = ('test_print_button',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:printer_id>/test-print/',
                self.admin_site.admin_view(trigger_test_print_view),
                name='control_printer_test_print',
            ),
        ]
        return custom_urls + urls

    def test_print_button(self, obj):
        if obj and obj.pk:
            url = reverse('admin:control_printer_test_print', args=[obj.pk])
            return format_html(
                '<button type="button" '
                'style="background-color: #417690; color: white; padding: 6px 12px; font-weight: bold; border-radius: 4px; border: none; cursor: pointer;" '
                'onclick="event.preventDefault(); event.stopPropagation(); '
                'fetch(\'{}\', {{'
                '    method: \'POST\', '
                '    headers: {{\'X-CSRFToken\': document.querySelector(\'[name=csrfmiddlewaretoken]\').value}}'
                '}}).then(function(){{ window.location.reload(); }});">'
                '🖨️ Send Test Print</button>',
                url
            )
        return "-"

    test_print_button.short_description = "Test Print"


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
