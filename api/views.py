import logging
import os

from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils.datetime_safe import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import PrintJobSerializer, PrinterSerializer, PrintRequestSerializer
from control.models import PrintJob, Printer, JobStatus, PrintingProperties
from printing.converter import detect_file_format, SUPPORTED_FILE_FORMATS
from printing.printing import print_file

logger = logging.getLogger('gutenberg.api.printing')


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class PrintJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PrintJobSerializer
    permission_classes = [IsAuthenticated]
    queryset = PrintJob.objects.all()
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = PrintJob.objects
        if not user.is_superuser:
            queryset = queryset.filter(owner=user)
        return queryset.all().order_by('date_created')

    @action(detail=False, methods=['post'], name='Submit new job')
    def submit(self, request):
        serializer = PrintRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        job = self._submit_printing_job(**serializer.validated_data)
        return Response(self.get_serializer(job).data)

    def _submit_printing_job(self, printer, file,
                             copies: int, pages_to_print: str,
                             color: bool, two_sides: str, **_):
        name, ext = os.path.splitext(file.name)
        name = slugify(name)
        file_name = '{}_{}_{}'.format(
            name, self.request.user.username,
            datetime.now().strftime(settings.PRINT_DATE_FORMAT))
        file_path = os.path.join(settings.PRINT_DIRECTORY, file_name + ext)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_type = detect_file_format(file_path)
        if file_type not in SUPPORTED_FILE_FORMATS:
            raise ValueError("Unsupported file type")
        job = PrintJob.objects.create(name=file.name, status=JobStatus.PENDING, owner=self.request.user,
                                      printer=printer)
        PrintingProperties.objects.create(color=color, copies=copies, two_sides=two_sides,
                                          pages_to_print=pages_to_print, job=job)

        print_file.delay(file_path, file_type, job.id)

        logger.info('User %s submitted file: "%s" (color printing: %s)',
                    self.request.user.username, file_path, color)
        return job


class PrinterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Printer.objects.all()
        if not user.is_superuser:
            queryset = queryset.filter(printerpermissions__group__user=user)
        return queryset.all().order_by('name')
