from django.conf import settings
from django.dispatch import receiver
from django_cas_ng.signals import cas_user_authenticated


@receiver(cas_user_authenticated)
def my_callback(sender, **kwargs):
    user = kwargs.pop('user')
    attributes = kwargs.pop('attributes')

    user.first_name = attributes[settings.FIRST_NAME_ATTR_NAME]
    user.last_name = attributes[settings.LAST_NAME_ATTR_NAME]
    user.is_superuser = settings.ADMIN_GROUP_NAME in attributes[
        settings.GROUPS_ATTR_NAME]

    user.save()
