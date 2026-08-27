import logging
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.serializers import (
    PrinterSerializer,
    GutenbergJobSerializer,
    JobArtefactSerializer,
)
from control.models import Printer, GutenbergJob, JobArtefact, JobStatus
from control.quotas import QuotaExceededException

logger = logging.getLogger('gutenberg.api')


class QuotaExceededAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Print quota exceeded.')
    default_code = 'quota_exceeded'


class PrinterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Printer.objects.filter_for_user(user)


class GutenbergJobViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GutenbergJobSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return GutenbergJob.objects.filter(owner=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except QuotaExceededException as exc:
            raise QuotaExceededAPIException(detail=str(exc))

    @action(detail=True, methods=['post'], url_path='continue-manual-duplex')
    def continue_manual_duplex(self, request, pk=None):
        """
        Triggers the second pass of a manual duplex print job.
        """
        job = self.get_object()

        if job.status != JobStatus.WAITING_FOR_USER_ACTION:
            return Response(
                {'error': 'Job is not waiting for manual duplex continuation.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from printing.tasks import print_job
        print_job.delay(job.id, is_manual_second_pass=True)

        return Response({'status': 'Second pass triggered.'}, status=status.HTTP_200_OK)


class JobArtefactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobArtefact.objects.all()
    serializer_class = JobArtefactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return JobArtefact.objects.filter(job__owner=self.request.user)
