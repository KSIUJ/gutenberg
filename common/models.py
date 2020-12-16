from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    api_key = models.CharField(max_length=100, blank=True, null=True)

    @property
    def can_color_print(self):
        return self.is_superuser
