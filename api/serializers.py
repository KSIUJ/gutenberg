from rest_framework import serializers

from common.models import User
from control.models import PrintJob, Printer, TwoSidedPrinting
from printing.converter import SUPPORTED_EXTENSIONS


class PrintJobSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField()
    printer = serializers.StringRelatedField()

    class Meta:
        model = PrintJob
        fields = '__all__'


class PrinterSerializer(serializers.ModelSerializer):
    supported_extensions = serializers.CharField(default=', '.join(sorted(SUPPORTED_EXTENSIONS)))

    class Meta:
        model = Printer
        fields = ['name', 'color_supported', 'duplex_supported', 'supported_extensions']


class PrintRequestSerializer(serializers.Serializer):
    printer = serializers.PrimaryKeyRelatedField(queryset=Printer.objects.all(), required=True)
    file = serializers.FileField(allow_empty_file=False, required=True)
    copies = serializers.IntegerField(required=True)
    pages_to_print = serializers.CharField(default=None)
    two_sides = serializers.ChoiceField(choices=TwoSidedPrinting.choices, required=True)
    color = serializers.BooleanField(default=False)


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'api_key']
