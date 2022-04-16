from django.contrib import admin

# Register your models here.
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, \
    JobArtefact


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class JobArtefactAdmin(admin.TabularInline):
    model = JobArtefact


class GutenbergJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, JobArtefactAdmin]


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
