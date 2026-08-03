"""Signal handlers for control models."""

from django.db.models.signals import post_delete
from django.db import transaction
from django.dispatch import receiver

from control.models import JobArtefact, PrintPreviewPage


@receiver(post_delete, sender=JobArtefact)
def delete_job_artefact_file(sender, instance, **kwargs):
    # FileField storage is not part of the DB transaction, so defer cleanup until commit.
    if instance.file and instance.file.name:
        file = instance.file
        transaction.on_commit(lambda: file.delete(save=False))


@receiver(post_delete, sender=PrintPreviewPage)
def delete_preview_page_file(sender, instance, **kwargs):
    # Empty FileFields have no storage path, so skip them.
    if instance.image and instance.image.name:
        image = instance.image
        transaction.on_commit(lambda: image.delete(save=False))
