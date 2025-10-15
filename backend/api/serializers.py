from rest_framework import serializers

from common.models import User
from control.models import GutenbergJob, Printer, TwoSidedPrinting, validate_pages_to_print, validate_n_up, \
    ImpositionTemplate, OrientationRequested, JobArtefact
from gutenberg.celery import app
from printing.processing.converter import get_formats_supported_by_workers


class GutenbergJobSerializer(serializers.ModelSerializer):
    printer = serializers.SlugRelatedField(slug_field='name', read_only=True)
    artefacts = serializers.SerializerMethodField()

    class Meta:
        model = GutenbergJob
        fields = ['id', 'pages', 'printer', 'status', 'status_reason', 'artefacts']

    def get_artefacts(self, obj):
        artefacts = obj.artefacts.all().order_by('document_number')
        request = self.context.get('request')
        return JobArtefactSerializer(artefacts, many=True, context={'request': request}).data


def _get_supported_extensions_default():
    return ",".join(sorted(
        get_formats_supported_by_workers(app).extensions,
    ))


class PrinterSerializer(serializers.ModelSerializer):
    supported_extensions = serializers.CharField(default=_get_supported_extensions_default)
    color_allowed = serializers.BooleanField()

    class Meta:
        model = Printer
        fields = ['id', 'name', 'color_allowed', 'duplex_supported', 'supported_extensions']

class CreatePrintJobRequestSerializer(serializers.Serializer):
    printer = serializers.IntegerField(required=True)
    copies = serializers.IntegerField(required=True)
    pages_to_print = serializers.CharField(allow_null=False, allow_blank=True, default="", validators=[validate_pages_to_print])
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, required=True)
    color = serializers.BooleanField(default=False)
    fit_to_page = serializers.BooleanField(default=True)
    n_up = serializers.IntegerField(default=1, validators=[validate_n_up])
    imposition_template = serializers.ChoiceField(choices=ImpositionTemplate.choices, default=ImpositionTemplate.NONE)
    orientation_requested = serializers.ChoiceField(choices=OrientationRequested.choices, default=OrientationRequested.AUTO)

class ChangePrintJobPropertiesRequestSerializer(serializers.Serializer):
    printer = serializers.IntegerField(required=False)
    copies = serializers.IntegerField(required=False)
    pages_to_print = serializers.CharField(required=False, allow_blank=True, validators=[validate_pages_to_print])
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, required=False)
    color = serializers.BooleanField(required=False)
    fit_to_page = serializers.BooleanField(required=False)
    n_up = serializers.IntegerField(required=False, validators=[validate_n_up])
    imposition_template = serializers.ChoiceField(required=False, choices=ImpositionTemplate.choices)
    orientation_requested = serializers.ChoiceField(required=False, choices=OrientationRequested.choices)


class UploadJobArtefactRequestSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, required=True)

class DeleteJobArtefactRequestSerializer(serializers.Serializer):
    artefact_id = serializers.IntegerField(required=True)

class ChangeArtefactOrderRequestSerializer(serializers.Serializer):
    new_order = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True
    )

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'api_key', 'is_staff']


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class JobArtefactSerializer(serializers.ModelSerializer):
    # Return the file URL
    file = serializers.FileField(read_only=True)

    class Meta:
        model = JobArtefact
        fields = ['id', 'file', 'artefact_type', 'mime_type', 'document_number']
