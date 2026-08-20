from rest_framework import serializers
from control.models import (
    GutenbergJob,
    Printer,
    PrintingProperties,
    JobArtefact,
    TwoSidedPrinting,
    ImpositionTemplate,
    OrientationRequested,
)
from common.models import User


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'api_key', 'is_staff']


class PrinterSerializer(serializers.ModelSerializer):
    color_allowed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Printer
        fields = ['id', 'name', 'color_supported', 'duplex_supported', 'color_allowed']


class PrintingPropertiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintingProperties
        fields = [
            'color',
            'copies',
            'two_sides',
            'pages_to_print',
            'fit_to_page',
            'n_up',
            'imposition_template',
            'orientation_requested',
        ]


class JobArtefactSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = JobArtefact
        fields = ['id', 'artefact_type', 'mime_type', 'document_number', 'file', 'url']

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class GutenbergJobSerializer(serializers.ModelSerializer):
    properties = PrintingPropertiesSerializer(read_only=True)
    artefacts = JobArtefactSerializer(many=True, read_only=True)
    printer_name = serializers.CharField(source='printer.name', read_only=True)

    class Meta:
        model = GutenbergJob
        fields = [
            'id',
            'name',
            'job_type',
            'printer',
            'printer_name',
            'owner',
            'pages',
            'status',
            'status_reason',
            'date_created',
            'date_processed',
            'date_finished',
            'properties',
            'artefacts',
            'preview_status',
            'preview_pages',
        ]


class CreatePrintJobRequestSerializer(serializers.Serializer):
    printer = serializers.IntegerField()
    copies = serializers.IntegerField(default=1, min_value=1)
    pages_to_print = serializers.CharField(required=False, allow_blank=True, default="")
    color = serializers.BooleanField(default=False)
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, default=TwoSidedPrinting.ONE_SIDED)
    fit_to_page = serializers.BooleanField(default=True)
    n_up = serializers.IntegerField(default=1)
    imposition_template = serializers.ChoiceField(choices=ImpositionTemplate.choices, default=ImpositionTemplate.NONE)
    orientation_requested = serializers.ChoiceField(choices=OrientationRequested.choices, default=OrientationRequested.AUTO)


class ChangePrintJobPropertiesRequestSerializer(serializers.Serializer):
    printer = serializers.IntegerField(required=False)
    copies = serializers.IntegerField(required=False, min_value=1)
    pages_to_print = serializers.CharField(required=False, allow_blank=True)
    color = serializers.BooleanField(required=False)
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, required=False)
    fit_to_page = serializers.BooleanField(required=False)
    n_up = serializers.IntegerField(required=False)
    imposition_template = serializers.ChoiceField(choices=ImpositionTemplate.choices, required=False)
    orientation_requested = serializers.ChoiceField(choices=OrientationRequested.choices, required=False)


class UploadJobArtefactRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
    preview = serializers.BooleanField(required=False, default=False)


class DeleteJobArtefactRequestSerializer(serializers.Serializer):
    artefact_id = serializers.IntegerField()


class ChangeArtefactOrderRequestSerializer(serializers.Serializer):
    new_order = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
