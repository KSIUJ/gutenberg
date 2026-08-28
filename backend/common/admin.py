from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms

from common.models import User
from control.models import UserQuotaOverride


class UserQuotaOverrideForm(forms.ModelForm):
    class Meta:
        model = UserQuotaOverride
        fields = '__all__'
        labels = {
            'daily_limit': 'Daily page limit',
            'weekly_limit': 'Weekly page limit',
            'monthly_limit': 'Monthly page limit',
        }
        help_texts = {
            'daily_limit': 'Leave blank to inherit the group page limit; 0 means unlimited.',
            'weekly_limit': 'Leave blank to inherit the group page limit; 0 means unlimited.',
            'monthly_limit': 'Leave blank to inherit the group page limit; 0 means unlimited.',
        }


class UserQuotaOverrideInline(admin.StackedInline):
    model = UserQuotaOverride
    form = UserQuotaOverrideForm
    max_num = 1
    extra = 0


class CommonUserAdmin(UserAdmin):
    inlines = [UserQuotaOverrideInline]


admin.site.register(User, CommonUserAdmin)
