from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django import forms

from control.forms import LocalPrinterParamsForm
# Register your models here.
from control.models import GutenbergJob, PrintingProperties, PrinterPermissions, LocalPrinterParams, Printer, \
    JobArtefact, GroupQuota


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


admin.site.register(Printer, PrinterAdmin)
admin.site.register(GutenbergJob, GutenbergJobAdmin)
admin.site.unregister(Group)
admin.site.register(Group, QuotaGroupAdmin)
