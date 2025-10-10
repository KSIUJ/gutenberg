from django.contrib import admin

from control.forms import LocalPrinterParamsForm
# Register your models here.
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, \
    JobArtefact


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


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
