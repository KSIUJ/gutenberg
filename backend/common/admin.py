from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from common.models import User
from control.models import UserQuotaOverride


class UserQuotaOverrideInline(admin.StackedInline):
    model = UserQuotaOverride
    max_num = 1
    extra = 0


class CommonUserAdmin(UserAdmin):
    inlines = [UserQuotaOverrideInline]


admin.site.register(User, CommonUserAdmin)
