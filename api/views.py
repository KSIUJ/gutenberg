import logging
from secrets import token_urlsafe
from typing import Optional

from django.contrib.auth import authenticate, login
from django.middleware.csrf import rotate_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import GutenbergJobSerializer, PrinterSerializer, PrintRequestSerializer, UserInfoSerializer, \
    CreatePrintJobRequestSerializer, UploadJobArtefactRequestSerializer, LoginSerializer, \
        DeleteJobArtefactRequestSerializer, ChangeArtefactOrderRequestSerializer
from common.models import User
from control.models import GutenbergJob, Printer, JobStatus, PrintingProperties, TwoSidedPrinting, JobArtefact, \
    JobArtefactType, JobType
from printing.converter import detect_file_format, SUPPORTED_FILE_FORMATS
from printing.printing import print_file

logger = logging.getLogger('gutenberg.api.printing')

def Error(error:str, message:str):
    return {error: message}

def Error(errors:dict):
    for k in errors:
        errors[k] = str(errors[k][0])
    return errors


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
            return Response(Error(serializer.errors),
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
            return Response(Error("status","JobStatus must be incoming"), status=status.HTTP_400_BAD_REQUEST)
        serializer = UploadJobArtefactRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(Error(serializer.errors),
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self._upload_artefact(job, **serializer.validated_data)
            #if serializer.validated_data['last'] == True:
            #    self._run_job(job)
        except UnsupportedDocumentError as ex:
            return Response(Error("document type",ex), status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(job).data)

    @action(detail=True, methods=['post'], name='Run job')
    def run_job(self, request, pk=None):
        job = self.get_object()
        #if job.status != JobStatus.INCOMING:
        #    return Response("Error: invalid job status for this request", status=status.HTTP_400_BAD_REQUEST)
        error = self._check_errors(job, job.properties)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        else:  
            self._run_job(job)
            #return job
            return Response(self.get_serializer(job).data)

    @action(detail=False, methods=['post'], name='Create new job')
    def create_job(self, request):
        serializer = CreatePrintJobRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(Error(serializer.errors),
                            status=status.HTTP_400_BAD_REQUEST)
        printer_with_perms = Printer.get_printer_for_user(user=self.request.user,
                                                          printer_id=serializer.validated_data['printer'])
        #if not printer_with_perms:
        #    return Response("Printer does not exist", status=status.HTTP_400_BAD_REQUEST)
        job = self._create_printing_job(printer_with_perms=printer_with_perms, **serializer.validated_data)
        return Response(self.get_serializer(job).data)
    
    @action(detail=True, methods=['post'], name='Change artefact order')
    def change_order(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            return Response(Error("status","JobStatus must be incoming"), status=status.HTTP_400_BAD_REQUEST)
        serializer = ChangeArtefactOrderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(Error(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        try:
            self._change_order(job, **serializer.validated_data)
        except Exception as ex:
            return Response(Error("order",str(ex)), status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(job).data)
        
    def _create_printing_job(self, printer_with_perms,
                             copies: int, pages_to_print: str,
                             color: bool, two_sides: str, fit_to_page: bool, **_):
        job = GutenbergJob.objects.create(name='webrequest', job_type=JobType.PRINT, status=JobStatus.INCOMING,
                                          owner=self.request.user, printer=printer_with_perms)
        #color = color if printer_with_perms.color_allowed else False
        #two_sides = two_sides if printer_with_perms.duplex_supported else TwoSidedPrinting.ONE_SIDED
        PrintingProperties.objects.create(color=color, copies=copies, two_sides=two_sides,
                                          pages_to_print=pages_to_print, job=job, fit_to_page=fit_to_page)
        return job

    def _upload_artefact(self, job, file, **_):
        last_artefact = job.artefacts.order_by('-order').first()
        order = last_artefact.order + 1 if last_artefact else 1

        artefact = JobArtefact.objects.create(job=job, artefact_type=JobArtefactType.SOURCE, file=file, order=order)
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
    
    def _change_order(self, job, new_order):
        for id in new_order:
            if not job.artefacts.filter(id=id).exists():
                raise ValueError(f"Artefact with id {id} does not exist in this job")
        if len(new_order) != job.artefacts.count():
            raise ValueError("New order list must contain all artefact IDs exactly once")
        
        idx = 1
        for id in new_order:
            artefact = job.artefacts.filter(id=id).first()
            artefact.order = idx
            artefact.save()
            idx += 1
        return job
    
    @action(detail=True, methods=['get'], name='Get artefacts')
    def artefacts(self, request, pk=None):
        job = self.get_object()
        artefacts = job.artefacts.all()
        artefact_data = [
            {
                "id": artefact.id,
                "file_name": artefact.file.name,
                "mime_type": artefact.mime_type,
                "artefact_type": artefact.artefact_type,
                "order": artefact.order
            }
            for artefact in artefacts
        ]
        return Response(artefact_data)

    @action(detail=True, methods=['delete'], name='Delete artefact')
    def delete_artefact(self, request, pk=None):
        job = self.get_object()
        serializer = DeleteJobArtefactRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(Error(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        artefact_id = serializer.validated_data['artefact_id']
        try:
            artefact = job.artefacts.get(id=artefact_id)
            artefact.delete()
            return Response({"message": f"Artefact {artefact_id} deleted successfully"}, status=status.HTTP_200_OK)
        except JobArtefact.DoesNotExist:
            return Response({"error": f"Artefact with id {artefact_id} does not exist"}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['get'], name='Get properties')
    def properties(self, request, pk=None):
        job = self.get_object()
        properties = PrintingProperties.objects.filter(job=job).first()
        if not properties:
            return Response("Error: job properties not found", status=status.HTTP_404_NOT_FOUND)
        return Response({
            "id": job.id,
            "status": job.status,
            "printer": job.printer.name,
            "copies": properties.copies,
            "pages_to_print": properties.pages_to_print,
            "color": properties.color,
            "two_sides": properties.two_sides,
            "fit_to_page": properties.fit_to_page
        })    
    
    @action(detail=True, methods=['post'], name="Change properties")
    def change_properties(self, request, pk=None):
        job = self.get_object()
        if job.status != JobStatus.INCOMING:
            return Response("Error: invalid job status for this request", status=status.HTTP_400_BAD_REQUEST)
        
        serializer = CreatePrintJobRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(Error(serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        
        error = self._check_errors(job, serializer.validated_data["printer"], PrintingProperties(
            color=serializer.validated_data['color'],
            copies=serializer.validated_data['copies'],
            two_sides=serializer.validated_data['two_sides'],
            pages_to_print=serializer.validated_data['pages_to_print'],
            fit_to_page=serializer.validated_data['fit_to_page']
        ))
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        properties = PrintingProperties.objects.get(job=job)
        job.printer = Printer.get_printer_for_user(user=self.request.user,
                                                   printer_id=serializer.validated_data['printer'])
        properties.copies = serializer.validated_data['copies']
        properties.pages_to_print = serializer.validated_data['pages_to_print']
        properties.color = serializer.validated_data['color']
        properties.two_sides = serializer.validated_data['two_sides']
        properties.fit_to_page = serializer.validated_data['fit_to_page']
        properties.save()

        return Response(self.get_serializer(job).data)
    
    
    @action(detail=True, methods=['get'], name='Validate job')
    def validate_job(self, request, pk=None):
        job = self.get_object()
        error = self._check_errors(job, job.printer, job.properties)
        
        return Response(error if error else {"error": None, "message": "Job is valid"}, 
                        status=status.HTTP_400_BAD_REQUEST if error else status.HTTP_200_OK)
        
    
    
    def _check_errors(self, job: GutenbergJob, printer, properties:PrintingProperties):
        errors={}
        
        if job.status != JobStatus.INCOMING:
            errors["status"] = "Job status must be INCOMING to validate"

        printer = Printer.get_printer_for_user(user=self.request.user, printer_id=job.printer.id)
        if not properties:
            errors["properties"] = "Job properties not found"

        if not printer:
            errors["printer"] = "Printer does not exist or you don't have permission to use it"
        if properties.color and not printer.color_allowed:
            errors["color"] = "Color printing is not allowed on this printer"
        if properties.two_sides != TwoSidedPrinting.ONE_SIDED and not printer.duplex_supported:
            errors["two_sides"] = "Two sided printing is not supported on this printer"
            
        return errors
        
        



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
        if not serializer.is_valid():
            return Response(Error(serializer.errors),
                            status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)
        if not user:
            return Response(data={'message': 'Username or password incorrect'}, status=403)
        if not user.is_active:
            return Response(data={'message': 'Account is not active'}, status=403)
        login(request, user)
        return Response(status=200)

    def get(self, request, *args, **kwargs):
        rotate_token(request)
        return Response(status=200)
