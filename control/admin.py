from django.contrib import admin

# Register your models here.
from control.models import PrintJob, PrintingProperties


class PrintingPropertiesInline(admin.TabularInline):
    model = PrintingProperties


class PrintJobAdmin(admin.ModelAdmin):
    inlines = [PrintingPropertiesInline, ]


admin.site.register(PrintJob, PrintJobAdmin)
