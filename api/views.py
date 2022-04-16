import logging
from secrets import token_urlsafe
from typing import Optional

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import GutenbergJobSerializer, PrinterSerializer, PrintRequestSerializer, UserInfoSerializer, \
    CreatePrintJobRequestSerializer, UploadJobArtefactRequestSerializer
from common.models import User
from control.models import GutenbergJob, Printer, JobStatus, PrintingProperties, TwoSidedPrinting, JobArtefact, \
    JobArtefactType, JobType
from printing.converter import detect_file_format, SUPPORTED_FILE_FORMATS
from printing.printing import print_file

logger = logging.getLogger('gutenberg.api.printing')


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 10000


class UnsupportedDocumentError(ValueError):
    pass


class PrintJobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GutenbergJobSerializer
    permission_classes = [IsAuthenticated]
    queryset = GutenbergJob.objects.all()
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        queryset = GutenbergJob.objects.filter(owner=user)
        return queryset.all().order_by('date_created')

    @action(detail=True, methods=['post'], name='Cancel job')
    def cancel(self, request, pk=None):
        job = self.get_object()
        GutenbergJob.objects.filter(id=job.id).filter(status=JobStatus.INCOMING).update(
            status=JobStatus.CANCELED)
        GutenbergJob.objects.filter(id=job.id).exclude(status__in=GutenbergJob.COMPLETED_STATUSES).update(
            status=JobStatus.CANCELING)
        return Response(self.get_serializer(job).data)

    @action(detail=False, methods=['post'], name='Submit new job')
    def submit(self, request):
        serializer = PrintRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=serializer.validated_data['printer'])
        if not printer_with_perms:
            return Response("Printer does not exist", status=status.HTTP_400_BAD_REQUEST)

        try:
            job = self._create_printing_job(printer_with_perms=printer_with_perms, **serializer.validated_data)
            self._upload_artefact(job, **serializer.validated_data)
            self._run_job(job)
        except UnsupportedDocumentError as ex:
            return Response("Error: {}".format(ex), status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Upload artefact')
    def upload_artefact(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            return Response("Error: invalid job status for this request", status=status.HTTP_400_BAD_REQUEST)
        serializer = UploadJobArtefactRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self._upload_artefact(job, **serializer.validated_data)
            if serializer.validated_data['last'] == True:
                self._run_job(job)
        except UnsupportedDocumentError as ex:
            return Response("Error: {}".format(ex), status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Run job')
    def run_job(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            return Response("Error: invalid job status for this request", status=status.HTTP_400_BAD_REQUEST)
        self._run_job(job)
        return job

    @action(detail=False, methods=['post'], name='Create new job')
    def create_job(self, request):
        serializer = CreatePrintJobRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=serializer.validated_data['printer'])
        if not printer_with_perms:
            return Response("Printer does not exist", status=status.HTTP_400_BAD_REQUEST)
        job = self._create_printing_job(printer_with_perms=printer_with_perms, **serializer.validated_data)
        return Response(self.get_serializer(job).data)

    def _create_printing_job(self, printer_with_perms,
                             copies: int, pages_to_print: str,
                             color: bool, two_sides: str, fit_to_page: bool, **_):
        job = GutenbergJob.objects.create(name='webrequest', job_type=JobType.PRINT, status=JobStatus.INCOMING,
                                          owner=self.request.user, printer=printer_with_perms)
        color = color if printer_with_perms.color_allowed else False
        two_sides = two_sides if printer_with_perms.duplex_supported else TwoSidedPrinting.ONE_SIDED
        PrintingProperties.objects.create(color=color, copies=copies, two_sides=two_sides,
                                          pages_to_print=pages_to_print, job=job, fit_to_page=fit_to_page)
        return job

    def _upload_artefact(self, job, file, **_):
        artefact = JobArtefact.objects.create(job=job, artefact_type=JobArtefactType.SOURCE, file=file)
        file_type = detect_file_format(artefact.file.path)
        if file_type not in SUPPORTED_FILE_FORMATS:
            raise UnsupportedDocumentError("Unsupported file type: {}".format(file_type))
        artefact.mime_type = file_type
        artefact.save()

    def _run_job(self, job):
        job.status = JobStatus.PENDING
        job.save()
        print_file.delay(job.id)
        logger.info('User %s submitted job: "%s"', self.request.user.username)
        return job


class PrinterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Printer.get_queryset_for_user(user).all().order_by('name')


def _generate_token():
    return token_urlsafe(32)


class MeView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserInfoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        if not self.request.user.api_key:
            self.request.user.api_key = _generate_token()
            self.request.user.save()
        return self.request.user


class ResetApiTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        self.request.user.api_key = _generate_token()
        self.request.user.save()
        return Response()
