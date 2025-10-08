import re
from math import log2

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q, IntegerField
from django.db.models.functions import Cast
from django.utils.translation import gettext_lazy as _

from common.models import User


class JobStatus(models.TextChoices):
    UNKNOWN = 'UNKNOWN', _('unknown')
    INCOMING = 'INCOMING', _('incoming')
    PENDING = 'PENDING', _('pending')
    PROCESSING = 'PROCESSING', _('processing')
    PRINTING = 'PRINTING', _('printing')
    # SCANNING = 'SCANNING', _('scanning')
    # WAITING_FOR_NEXT_PAGE = 'WAITING_PAGE', _('waiting for next page')
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


class ImpositionTemplate(models.TextChoices):
    NONE = 'none', _('none'),
    BOOKLET = 'booklet', _('booklet')


class OrientationRequested(models.TextChoices):
    AUTO = 'AUTO', _('auto')
    PORTRAIT = 'PORTRAIT', _('portrait')
    LANDSCAPE = 'LANDSCAPE', _('landscape')


# class ScannerType(models.TextChoices):
#     DISABLED = 'NA', _('disabled')
#     LOCAL_SCANIMAGE = 'SC', _('local scanimage')


class Printer(models.Model):
    name = models.CharField(max_length=64)
    printer_type = models.CharField(max_length=10, default=PrinterType.DISABLED, choices=PrinterType.choices)
    color_supported = models.BooleanField(default=False)
    duplex_supported = models.BooleanField(default=False)

    @staticmethod
    def get_queryset_for_user(user):
        queryset = Printer.objects
        return queryset.filter(printerpermissions__group__user=user).annotate(
            color_allowed=Cast(F('color_supported'), output_field=IntegerField()) * Max(
                Cast('printerpermissions__print_color', output_field=IntegerField()),
                filter=Q(printerpermissions__group__user=user)))

    @staticmethod
    def get_printer_for_user(user, printer_id):
        return Printer.get_queryset_for_user(user).filter(id=printer_id).first()

    def __str__(self):
        return '{} ({})'.format(self.name, self.get_printer_type_display())


# class Scaner(models.Model):
#     name = models.CharField(max_length=64)
#     scaner_type = models.CharField(max_length=10, default=ScannerType.DISABLED, choices=ScannerType.choices)
#     color_supported = models.BooleanField(default=False)
#     duplex_supported = models.BooleanField(default=False)
#
#     def __str__(self):
#         return '{} ({})'.format(self.name, self.get_scaner_type_display())
#

class LocalPrinterParams(models.Model):
    printer = models.OneToOneField(Printer, on_delete=models.CASCADE)

    cups_printer_name = models.CharField(max_length=128)
    print_grayscale_param = models.CharField(max_length=64, null=True, blank=True)
    print_color_param = models.CharField(max_length=64, null=True, blank=True)
    print_one_sided_param = models.CharField(max_length=64, null=True, blank=True)
    print_two_sided_long_edge_param = models.CharField(max_length=64, null=True, blank=True)
    print_two_sided_short_edge_param = models.CharField(max_length=64, null=True, blank=True)


# class LocalScanerParams(models.Model):
#     scaner = models.OneToOneField(Scaner, on_delete=models.CASCADE)
#
#     scanimage_name = models.CharField(max_length=128)


class PrinterPermissions(models.Model):
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    print_color = models.BooleanField(default=False)

    def __str__(self):
        return '{} - {}'.format(self.printer, self.group)

    class Meta:
        unique_together = ('printer', 'group')


# class ScanerPermissions(models.Model):
#     scaner = models.ForeignKey(Scaner, on_delete=models.CASCADE)
#     group = models.ForeignKey(Group, on_delete=models.CASCADE)
#
#     def __str__(self):
#         return '{} - {}'.format(self.scaner, self.group)
#
#     class Meta:
#         unique_together = ('scaner', 'group')


class JobType(models.TextChoices):
    UNKNOWN = 'NA', _('unknown')
    PRINT = 'PRINT', _('print')
    # SCAN = 'SCAN', _('scan')
    # COPY = 'COPY', _('copy')


class GutenbergJob(models.Model):
    name = models.CharField(max_length=128)
    job_type = models.CharField(max_length=10, default=JobType.UNKNOWN, choices=JobType.choices)
    printer = models.ForeignKey(Printer, null=True, blank=True, on_delete=models.SET_NULL)
    # scaner = models.ForeignKey(Scaner, null=True, blank=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    pages = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=12, default=JobStatus.UNKNOWN, choices=JobStatus.choices)
    status_reason = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_processed = models.DateTimeField(null=True, blank=True)
    date_finished = models.DateTimeField(null=True, blank=True)
    next_document_number = models.IntegerField(default=1)

    def __str__(self):
        return "{} - {} - {} - {}".format(self.date_created, self.job_type, self.name, self.owner)

    COMPLETED_STATUSES = [JobStatus.COMPLETED, JobStatus.CANCELED, JobStatus.ERROR, JobStatus.UNKNOWN]

    @property
    def completed(self):
        return self.status in self.COMPLETED_STATUSES

    @property
    def not_completed(self):
        return not self.completed


class JobArtefactType(models.TextChoices):
    SOURCE = 'SC', _('source')
    INTERMEDIATE = 'IN', _('intermediate')
    FINAL = 'OU', _('output')


class JobArtefact(models.Model):
    job = models.ForeignKey(GutenbergJob, on_delete=models.CASCADE, related_name='artefacts')
    file = models.FileField(upload_to='artefacts/%Y/%m/%d/')
    artefact_type = models.CharField(max_length=4, default=JobArtefactType.SOURCE, choices=JobArtefactType.choices)
    mime_type = models.CharField(max_length=100, default='application/octet-stream')
    #document ordering starts from 1, 0 means something went wrong
    document_number = models.IntegerField(default=0)

    def __str__(self):
        return self.file.name


def validate_pages_to_print(value):
    code = 'invalid'
    if not re.search(r'^\d+(?:-\d+)?(,\d+(?:-\d+)?)*$', str(value)):
        raise ValidationError('Invalid page selection string: {}'.format(value), code=code)
    # Check for invalid page ranges (e.g. 3-1)
    parts = [part.split('-') for part in value.split(',')]
    for part in parts:
        # In case of single page numbers, part[0] and part[-1] is the
        # same thing, so we don't have to separately check for that
        if int(part[0]) > int(part[-1]) or int(part[0]) < 1:
            raise ValidationError('Invalid page range: {}-{}'.format(part[0], part[-1]), code)


def validate_n_up(value: int):
    divide_count = round(log2(value))
    if 2 ** divide_count != value:
        raise ValueError("n_up value must be a power of 2")


class PrintingProperties(models.Model):
    color = models.BooleanField(default=False)
    copies = models.IntegerField(default=1)
    two_sides = models.CharField(max_length=2, default=TwoSidedPrinting.ONE_SIDED, choices=TwoSidedPrinting.choices)
    pages_to_print = models.CharField(max_length=100, null=True, blank=True, validators=[validate_pages_to_print])
    job = models.OneToOneField(GutenbergJob, on_delete=models.CASCADE, related_name='properties')
    fit_to_page = models.BooleanField(default=True)
    n_up = models.IntegerField(default=1, validators=[validate_n_up])
    imposition_template = models.CharField(default=ImpositionTemplate.NONE, choices=ImpositionTemplate.choices)
    orientation_requested = models.CharField(default=OrientationRequested.AUTO, choices=OrientationRequested.choices)
