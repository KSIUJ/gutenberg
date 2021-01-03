from rest_framework import serializers

from common.models import User
from control.models import PrintJob, Printer, TwoSidedPrinting
from printing.converter import SUPPORTED_EXTENSIONS


class PrintJobSerializer(serializers.ModelSerializer):
    printer = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = PrintJob
        fields = ['id', 'pages', 'printer', 'status', 'status_reason']


class PrinterSerializer(serializers.ModelSerializer):
    supported_extensions = serializers.CharField(default=', '.join(sorted(SUPPORTED_EXTENSIONS)))
    color_allowed = serializers.BooleanField()

    class Meta:
        model = Printer
        fields = ['id', 'name', 'color_allowed', 'duplex_supported', 'supported_extensions']


class PrintRequestSerializer(serializers.Serializer):
    printer = serializers.IntegerField(required=True)
    file = serializers.FileField(allow_empty_file=False, required=True)
    copies = serializers.IntegerField(required=True)
    pages_to_print = serializers.CharField(default=None)
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, required=True)
    color = serializers.BooleanField(default=False)


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'api_key', 'is_staff']
