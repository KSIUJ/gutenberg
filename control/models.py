import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import User


class JobStatus(models.TextChoices):
    UNKNOWN = 'UNKNOWN', _('unknown')
    INCOMING = 'INCOMING', _('incoming')
    PENDING = 'PENDING', _('pending')
    PROCESSING = 'PROCESSING', _('processing')
    PRINTING = 'PRINTING', _('printing')
    COMPLETED = 'COMPLETED', _('completed')
    CANCELED = 'CANCELED', _('canceled')
    CANCELING = 'CANCELING', _('canceling')
    ERROR = 'ERROR', _('error')


class TwoSidedPrinting(models.TextChoices):
    ONE_SIDED = 'OS', _('one sided')
    TWO_SIDED_LONG_EDGE = 'TL', _('two sided long edge')
    TWO_SIDED_SHORT_EDGE = 'TS', _('two sided short edge')


class PrintJob(models.Model):
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    pages = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, default=JobStatus.UNKNOWN, choices=JobStatus.choices)
    status_reason = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{} - {} - {}".format(self.date_created, self.name, self.owner)

    COMPLETED_STATUSES = [JobStatus.COMPLETED, JobStatus.CANCELED, JobStatus.ERROR, JobStatus.UNKNOWN]

    @property
    def completed(self):
        return self.status in self.COMPLETED_STATUSES

    @property
    def not_completed(self):
        return not self.completed

    def get_artifact_storage(self):
        path = os.path.join(settings.PRINT_DIRECTORY, str(self.id))
        return FileSystemStorage(location=path)


class PrintingProperties(models.Model):
    color = models.BooleanField(default=False)
    copies = models.IntegerField(default=1)
    two_sides = models.CharField(max_length=2, default=TwoSidedPrinting.ONE_SIDED, choices=TwoSidedPrinting.choices)
    pages_to_print = models.CharField(max_length=100, null=True, blank=True)
    job = models.OneToOneField(PrintJob, on_delete=models.CASCADE, related_name='properties')
