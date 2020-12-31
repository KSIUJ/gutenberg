from django.contrib import admin

# Register your models here.
from control.models import PrintJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class PrintJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, ]


class LocalPrinterParamsInline(admin.StackedInline):
    model = LocalPrinterParams


class PrinterPermissionsAdmin(admin.TabularInline):
    model = PrinterPermissions


class PrinterAdmin(admin.ModelAdmin):
    inlines = [LocalPrinterParamsInline, PrinterPermissionsAdmin]


admin.site.register(Printer, PrinterAdmin)
admin.site.register(PrintJob, PrintJobAdmin)
