import os
from enum import Enum
from typing import Set

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import F, Max, Count, Q
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


class PrinterType(models.TextChoices):
    DISABLED = 'NA', _('disabled')
    LOCAL_CUPS = 'LP', _('local cups')


class Printer(models.Model):
    name = models.CharField(max_length=64)
    printer_type = models.CharField(max_length=10, default=PrinterType.DISABLED, choices=PrinterType.choices)
    color_supported = models.BooleanField(default=False)
    duplex_supported = models.BooleanField(default=False)

    @staticmethod
    def get_queryset_for_user(user):
        queryset = Printer.objects
        if not user.is_superuser:
            return queryset.filter(printerpermissions__group__user=user).annotate(
                color_allowed=F('color_supported') * Max('printerpermissions__print_color',
                                                         filter=Q(printerpermissions__group__user=user)))
        else:
            return queryset.annotate(color_allowed=F('color_supported'))

    @staticmethod
    def get_printer_for_user(user, printer_id):
        return Printer.get_queryset_for_user(user).filter(id=printer_id).first()

    def __str__(self):
        return '{} ({})'.format(self.name, self.get_printer_type_display())


class LocalPrinterParams(models.Model):
    printer = models.OneToOneField(Printer, on_delete=models.CASCADE)

    cups_printer_name = models.CharField(max_length=128)
    print_grayscale_param = models.CharField(max_length=64, null=True, blank=True)
    print_color_param = models.CharField(max_length=64, null=True, blank=True)
    print_one_sided_param = models.CharField(max_length=64, null=True, blank=True)
    print_two_sided_long_edge_param = models.CharField(max_length=64, null=True, blank=True)
    print_two_sided_short_edge_param = models.CharField(max_length=64, null=True, blank=True)


class PrinterPermissions(models.Model):
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    print_color = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {}'.format(self.printer, self.group)

    class Meta:
        unique_together = ('printer', 'group')


class PrintJob(models.Model):
    name = models.CharField(max_length=128)
    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    pages = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, default=JobStatus.UNKNOWN, choices=JobStatus.choices)
    status_reason = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_finished = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{} - {} - {} - {}".format(self.date_created, self.printer, self.name, self.owner)

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
