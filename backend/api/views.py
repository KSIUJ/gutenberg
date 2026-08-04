import logging
import os
import tempfile
from secrets import token_urlsafe

from celery import current_app
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import F
from django.middleware.csrf import rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import viewsets, status, exceptions
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.exceptions import UnsupportedDocument, InvalidStatus
from api.serializers import GutenbergJobSerializer, PrinterSerializer, UserInfoSerializer, \
    CreatePrintJobRequestSerializer, UploadJobArtefactRequestSerializer, LoginSerializer, \
    DeleteJobArtefactRequestSerializer, ChangeArtefactOrderRequestSerializer, JobArtefactSerializer, \
    ChangePrintJobPropertiesRequestSerializer, PrintPreviewSerializer
from common.models import User
from control.models import GutenbergJob, Printer, JobStatus, PrintingProperties, TwoSidedPrinting, JobArtefact, \
    JobArtefactType, JobType, PrintPreview, PreviewStatus
from gutenberg.worker_capabilities import get_formats_supported_by_workers
from printing.printing import print_file
from printing.preview import generate_preview
from printing.processing.converter import detect_file_format

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
        job.refresh_from_db()
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Upload artefact')
    def upload_artefact(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            raise InvalidStatus("Invalid job status for this request", additional_info="current status: {}".format(job.status))
        serializer = UploadJobArtefactRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            self._upload_artefact(job, **serializer.validated_data)
        except UnsupportedDocumentError as ex:
            raise UnsupportedDocument(str(ex))
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['delete'], name='Delete artefact')
    def delete_artefact(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            raise InvalidStatus("Invalid job status for this request", additional_info="current status: {}".format(job.status))
        serializer = DeleteJobArtefactRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        artefact_id = serializer.validated_data['artefact_id']
        artefact = JobArtefact.objects.filter(id=artefact_id, job=job).first()
        if not artefact:
            raise exceptions.NotFound("Selected artefact does not exist")
        with transaction.atomic():
            artefact.delete()
            self._mark_configuration_changed(job)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Change artefact order')
    def change_artefact_order(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            raise InvalidStatus("Invalid job status for this request", additional_info="current status: {}".format(job.status))
        serializer = ChangeArtefactOrderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job = self._change_order(**serializer.validated_data)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Run job')
    def run_job(self, request, pk=None):
        job = self.get_object()
        self._validate_properties(job.printer.id, job.properties, job)
        self._run_job(job)
        return Response(self.get_serializer(job).data)

    @action(detail=False, methods=['post'], name='Create new job')
    def create_job(self, request):
        serializer = CreatePrintJobRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=serializer.validated_data['printer'])
        if not printer_with_perms:
            raise exceptions.NotFound("Selected printer does not exist")
        job = self._create_printing_job(printer_with_perms=printer_with_perms, **serializer.validated_data)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Change job properties')
    def change_properties(self, request, pk=None):
        # Not given fields are not changed
        job = self.get_object()
        serializer = ChangePrintJobPropertiesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        printer_id=serializer.validated_data.get('printer')
        if printer_id is None:
            printer_id=job.printer.id
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=printer_id)
        job = self._change_properties(printer_with_perms=printer_with_perms, **serializer.validated_data)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['get'], name='Validate job properties')
    def validate_properties(self, request, pk=None):
        job = self.get_object()
        self._validate_properties(job.printer.id, job.properties, job)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['get'], name='List artefacts')
    def artefacts(self, request, pk=None):
        job = self.get_object()
        artefacts = job.artefacts.all().order_by('document_number')
        serializer = JobArtefactSerializer(artefacts, many=True, context={'request': request})
        return Response(serializer.data)

    def _create_printing_job(
        self,
        printer_with_perms,
        copies: int,
        pages_to_print: str,
        color: bool,
        two_sides: str,
        fit_to_page: bool,
        n_up: int,
        imposition_template: str,
        orientation_requested: str,
        **_,
    ):
        with transaction.atomic():
            job = GutenbergJob(name='webrequest', job_type=JobType.PRINT, status=JobStatus.INCOMING,
                                              owner=self.request.user, printer=printer_with_perms)
            job.properties = PrintingProperties(
                color=color,
                copies=copies,
                two_sides=two_sides,
                pages_to_print=None if pages_to_print == "" else pages_to_print,
                job=job,
                fit_to_page=fit_to_page,
                n_up=n_up,
                imposition_template=imposition_template,
                orientation_requested=orientation_requested,
            )

            self._validate_properties(printer_with_perms.id, job.properties, job)
            job.save()
            job.properties.save()
            return job

    def _change_properties(
        self,
        printer_with_perms = None,
        copies: int = None,
        pages_to_print: str = None,
        color: bool = None,
        two_sides: str = None,
        fit_to_page: bool = None,
        n_up: int = None,
        imposition_template: str = None,
        orientation_requested: str = None,
        **_,
    ):
        job = self.get_object()
        with transaction.atomic():
            if printer_with_perms is not None:
                job.printer = printer_with_perms
            if color is not None:
                job.properties.color = color
            if copies is not None:
                job.properties.copies = copies
            if two_sides is not None:
                job.properties.two_sides = two_sides
            if pages_to_print is not None:
                job.properties.pages_to_print = None if pages_to_print == "" else pages_to_print
            if fit_to_page is not None:
                job.properties.fit_to_page = fit_to_page
            if n_up is not None:
                job.properties.n_up = n_up
            if imposition_template is not None:
                job.properties.imposition_template = imposition_template
            if orientation_requested is not None:
                job.properties.orientation_requested = orientation_requested

            self._validate_properties(job.printer.id, job.properties, job=job)
            job.properties.save()
            job.save()
            self._mark_configuration_changed(job)
        return job

    def _upload_artefact(self, job, file, **_):
        # `detect_file_format()` needs a real file path, while uploaded files may
        # be in-memory streams, so copy the upload to a temp file just for sniffing.
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        artefact = None
        try:
            file_type = detect_file_format(temp_path)
        finally:
            os.unlink(temp_path)

        if file_type not in get_formats_supported_by_workers()["mime_types"]:
            raise UnsupportedDocumentError("Unsupported file type: {}".format(file_type))

        try:
            with transaction.atomic():
                file.seek(0)
                artefact = JobArtefact.objects.create(
                    job=job,
                    artefact_type=JobArtefactType.SOURCE,
                    file=file,
                    document_number=job.next_document_number,
                )
                job.next_document_number += 1
                job.save(update_fields=['next_document_number'])
                artefact.mime_type = file_type
                artefact.save(update_fields=['mime_type'])
                self._mark_configuration_changed(job)
        except Exception:
            if artefact is not None and artefact.file.name:
                artefact.file.delete(save=False)
            raise

    def _change_order(self, new_order):
        job = self.get_object()
        with transaction.atomic():
            artefacts = list(job.artefacts.all())
            artefact_dict = {artefact.id: artefact for artefact in artefacts}
            if set(new_order) != set(artefact_dict.keys()):
                raise exceptions.ValidationError("New order does not match existing artefacts")
            if len(set(new_order)) != len(new_order):
                raise exceptions.ValidationError("New order contains duplicate artefact IDs")
            for index, artefact_id in enumerate(new_order):
                artefact = artefact_dict[artefact_id]
                artefact.document_number = index + 1
                artefact.save()
            job.next_document_number = len(new_order) + 1
            job.save()
            self._mark_configuration_changed(job)
        return job

    def _run_job(self, job):
        try:
            preview = job.preview
        except PrintPreview.DoesNotExist:
            preview = None

        if preview is not None:
            if preview.status in (PreviewStatus.PENDING, PreviewStatus.PROCESSING):
                if preview.celery_task_id:
                    current_app.control.revoke(
                        preview.celery_task_id,
                        terminate=False,
                    )
                preview.status = PreviewStatus.CANCELED
                preview.save(update_fields=['status', 'updated_at'])

        job.status = JobStatus.PENDING
        job.save()
        print_file.delay(job.id)
        logger.info('User %s submitted job: %s', self.request.user.username, job.id)
        return job

    def _validate_properties(self, printer_id: int, properties, job):
        if job.status != JobStatus.INCOMING:
            raise InvalidStatus("Invalid job status for this request", additional_info="current status: {}".format(job.status))
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=printer_id)
        if not printer_with_perms:
            raise exceptions.NotFound("Selected printer does not exist")
        if properties.color and not printer_with_perms.color_allowed:
            raise exceptions.ValidationError("Color printing is not allowed on the selected printer")
        if properties.two_sides != TwoSidedPrinting.ONE_SIDED and not printer_with_perms.duplex_supported:
            raise exceptions.ValidationError("Two-sided printing is not supported on the selected printer")

    @action(
        detail=True,
        methods=['get'],
        url_path='preview',
        name='Print preview',
    )
    def preview(self, request, pk=None):
        job = self.get_object()

        try:
            preview = job.preview
        except PrintPreview.DoesNotExist:
            raise exceptions.NotFound(
                'A preview has not been requested for this job'
            )

        serializer = PrintPreviewSerializer(preview, context={'request': request})
        return Response(serializer.data)

    # Split the mutating methods so DRF shows separate browsable API forms.
    @preview.mapping.post
    def preview_post(self, request, pk=None):
        job = self.get_object()

        if job.status != JobStatus.INCOMING:
            raise InvalidStatus(
                'Preview can only be generated for an incoming job',
                additional_info=f'current status: {job.status}',
            )

        if not job.artefacts.filter(artefact_type=JobArtefactType.SOURCE).exists():
            raise exceptions.ValidationError(
                'The print job does not contain any documents'
            )

        self._validate_properties(job.printer.id, job.properties, job)

        with transaction.atomic():
            preview = PrintPreview.objects.select_for_update().filter(job=job).first()

            previous_task_id = ''

            if preview is None:
                preview = PrintPreview.objects.create(
                    job=job,
                    status=PreviewStatus.PENDING,
                    generation=1,
                    configuration_version=job.configuration_version,
                )
            else:
                previous_task_id = preview.celery_task_id
                preview.generation += 1
                preview.configuration_version = job.configuration_version
                preview.status = PreviewStatus.PENDING
                preview.error = ''
                preview.celery_task_id = ''
                preview.pages.all().delete()
                preview.save()

            generation = preview.generation

        if previous_task_id:
            current_app.control.revoke(previous_task_id, terminate=False)

        task = generate_preview.delay(preview.id, generation)

        preview.celery_task_id = task.id
        preview.save(update_fields=['celery_task_id', 'updated_at'])

        serializer = PrintPreviewSerializer(preview, context={'request': request})
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @preview.mapping.delete
    def preview_delete(self, request, pk=None):
        job = self.get_object()

        try:
            preview = job.preview
        except PrintPreview.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        if preview.celery_task_id:
            current_app.control.revoke(preview.celery_task_id, terminate=False)

        preview.status = PreviewStatus.CANCELED
        preview.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def _mark_configuration_changed(job):
        GutenbergJob.objects.filter(id=job.id).update(
            configuration_version=F('configuration_version') + 1
        )
        job.refresh_from_db(fields=['configuration_version'])


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
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginApiView(APIView):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(APIView, cls).as_view(**initkwargs)
        view.cls = cls
        view.initkwargs = initkwargs
        return view

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)
        if not user:
            raise exceptions.PermissionDenied("Invalid username or password")
        if not user.is_active:
            raise exceptions.PermissionDenied("Account is not active")
        login(request, user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, *args, **kwargs):
        """
        Rotate the CSRF token. According to the `rotate_token` function documentation,
        it should always be called on login.
        """
        rotate_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotFoundView(APIView):
    def _handle(self, request, path):
        raise exceptions.NotFound(f'API route "{path}" not found')

    get = _handle
    post = _handle
    put = _handle
    patch = _handle
    delete = _handle
