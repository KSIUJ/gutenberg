from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from common.models import User


class CommonUserAdmin(UserAdmin):
    pass


admin.site.register(User, CommonUserAdmin)
