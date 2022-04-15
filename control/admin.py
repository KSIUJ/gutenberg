from django.contrib import admin

# Register your models here.
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class GutenbergJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, ]


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
