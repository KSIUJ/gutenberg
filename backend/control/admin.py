from django.contrib import admin

from control.forms import LocalPrinterParamsForm
from control.models import (
    GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, JobArtefact
)


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class JobArtefactAdmin(admin.TabularInline):
    model = JobArtefact


class GutenbergJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, JobArtefactAdmin]
    readonly_fields = ('pages', 'date_created', 'date_processed', 'date_finished', 'manual_duplex_current_pass')
    list_display = ('date_created', 'owner', 'name', 'job_type', 'status', 'manual_duplex_current_pass', 'pages')
    list_filter = ('date_created', 'owner', 'job_type', 'status')


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams
    form = LocalPrinterParamsForm
    fieldsets = (
        (None, {
            'fields': (
                'cups_printer_name', 'print_grayscale_param', 'print_color_param',
                'print_one_sided_param', 'print_two_sided_long_edge_param', 'print_two_sided_short_edge_param'
            )
        }),
        ('Manual Duplex Settings', {
            'fields': (
                'manual_duplex_enabled',
                'manual_duplex_first_pass',
                'manual_duplex_first_pass_reverse',
                'manual_duplex_second_pass_reverse',
                'manual_duplex_face_orientation',
                'manual_duplex_feed_edge',
            )
        }),
    )


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
