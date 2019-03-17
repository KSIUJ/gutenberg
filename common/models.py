from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    @property
    def can_color_print(self):
        return self.is_superuser
