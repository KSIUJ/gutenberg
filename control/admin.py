from django.contrib import admin

# Register your models here.
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, \
    JobArtefact


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class JobArtefactAdmin(admin.TabularInline):
    model = JobArtefact
    inlines = [PrintingPropertiesInline]  # Add PrintingPropertiesInline here


class GutenbergJobAdmin(admin.ModelAdmin):
    inlines = [JobArtefactAdmin]  # Removed PrintingPropertiesInline
    readonly_fields = ('pages', 'date_created', 'date_processed', 'date_finished')
    list_display = ('date_created', 'owner', 'name', 'job_type', 'status', 'pages')
    list_filter = ('date_created', 'owner', 'job_type', 'status')


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
