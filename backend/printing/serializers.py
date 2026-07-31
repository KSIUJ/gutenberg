from rest_framework import serializers
from .models import PrintJob

class PrintJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintJob
        fields = ['id','user','uploaded_file','created_at','preview_status','preview_pages','preview_meta','settings','printed_at','ipp_job_id']
        read_only_fields = ['id','created_at','preview_status','preview_pages','preview_meta','printed_at','ipp_job_id']

class PrintJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintJob
        fields = ['id','uploaded_file','settings']
