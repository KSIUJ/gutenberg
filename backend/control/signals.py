"""Signal handlers for control models."""

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from control.models import JobArtefact, PrintPreviewPage

@receiver(post_delete, sender=JobArtefact)
def delete_job_artefact_file(sender, instance, **kwargs):
    if instance.file and instance.file.name:
        file = instance.file
        transaction.on_commit(lambda: file.delete(save=False))


@receiver(post_delete, sender=PrintPreviewPage)
def delete_preview_page_file(sender, instance, **kwargs):
    if instance.image and instance.image.name:
        image = instance.image
        transaction.on_commit(lambda: image.delete(save=False))
