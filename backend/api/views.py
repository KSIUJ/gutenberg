import logging
from secrets import token_urlsafe

from django.contrib.auth import authenticate, login
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
    ChangePrintJobPropertiesRequestSerializer
from common.models import User
from control.models import GutenbergJob, Printer, JobStatus, PrintingProperties, TwoSidedPrinting, JobArtefact, \
    JobArtefactType, JobType
from printing.printing import print_file
from printing.processing.converter import detect_file_format, SUPPORTED_FILE_FORMATS

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
        artefact.delete()
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
        self._validate_properties(job.printer, job.properties)
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
        #not given fields are not changed
        job = self.get_object()
        serializer = ChangePrintJobPropertiesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        printer=serializer.validated_data.get('printer')
        if printer is None:
            printer=job.printer.id
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=printer)
        job = self._change_properties(printer_with_perms=printer_with_perms, **serializer.validated_data)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['get'], name='Validate job properties')
    def validate_properties(self, request, pk=None):
        job = self.get_object()
        self._validate_properties(job.printer.id, job.properties)
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
        job = GutenbergJob(name='webrequest', job_type=JobType.PRINT, status=JobStatus.INCOMING,
                                          owner=self.request.user, printer=printer_with_perms)
        job.properties = PrintingProperties(
            color=color,
            copies=copies,
            two_sides=two_sides,
            pages_to_print=pages_to_print,
            job=job,
            fit_to_page=fit_to_page,
            n_up=n_up,
            imposition_template=imposition_template,
            orientation_requested=orientation_requested,
        )

        self._validate_properties(printer_with_perms.id, job.properties)
        job.properties.save()
        job.save()
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
        if printer_with_perms is not None:
            job.printer = printer_with_perms
        if color is not None:
            job.properties.color = color
        if copies is not None:
            job.properties.copies = copies
        if two_sides is not None:
            job.properties.two_sides = two_sides
        if pages_to_print is not None:
            job.properties.pages_to_print = pages_to_print
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
        return job

    def _upload_artefact(self, job, file, **_):
        artefact = JobArtefact.objects.create(job=job, artefact_type=JobArtefactType.SOURCE, file=file, document_number=job.next_document_number)
        job.next_document_number += 1
        job.save()
        file_type = detect_file_format(artefact.file.path)
        if file_type not in SUPPORTED_FILE_FORMATS:
            raise UnsupportedDocumentError("Unsupported file type: {}".format(file_type))
        artefact.mime_type = file_type
        artefact.save()

    def _change_order(self, new_order):
        job = self.get_object()
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
        return job

    def _run_job(self, job):
        job.status = JobStatus.PENDING
        job.save()
        print_file.delay(job.id)
        logger.info('User %s submitted job: %s', self.request.user.username, job.id)
        return job

    def _validate_properties(self, printer:int , properties, job=None):
        if job is None:
            job = self.get_object()
        if job.status != JobStatus.INCOMING:
            raise InvalidStatus("Invalid job status for this request", additional_info="current status: {}".format(job.status))
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=printer)
        if not printer_with_perms:
            raise exceptions.NotFound("Selected printer does not exist")
        if properties.color and not printer_with_perms.color_allowed:
            raise exceptions.ValidationError("Color printing is not allowed on the selected printer")
        if properties.two_sides != TwoSidedPrinting.ONE_SIDED and not printer_with_perms.duplex_supported:
            raise exceptions.ValidationError("Two-sided printing is not supported on the selected printer")


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
