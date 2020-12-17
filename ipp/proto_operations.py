from django.utils import timezone

from ipp import SUPPORTED_IPP_FORMATS, DEFAULT_IPP_FORMAT
from ipp.constants import SectionEnum, OperationEnum, FinishingEnum, PageOrientationEnum, PrintQualityEnum
from ipp.fields import MimeTypeField, UriField, CharsetField, OneSetField, BooleanField, KeywordField, NaturalLangField, \
    IntegerField, EnumField, TextWLField, DateTimeField, NameWLField, IntRangeField, IntRange, ResolutionField, \
    Resolution, OctetStringField
from ipp.proto import BaseOperationGroup, AttributeGroup, ipp_timestamp, MergedGroup


class GetPrinterAttributesRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField(required=True)
    document_format = MimeTypeField()


class PrinterDescriptionGroup(AttributeGroup):
    _tag = SectionEnum.printer
    _filter = 'printer-description'

    # default
    charset_configured = CharsetField(required=True, default='utf-8')
    charset_supported = OneSetField(accepted_fields=[CharsetField()], required=True, default=['utf-8'])
    color_supported = BooleanField(default=True)
    compression_supported = OneSetField(accepted_fields=[KeywordField()], required=True, default=['none'])
    document_format_supported = OneSetField(accepted_fields=[MimeTypeField()], required=True,
                                            default=SUPPORTED_IPP_FORMATS)
    document_format_default = MimeTypeField(required=True, default=DEFAULT_IPP_FORMAT)
    generated_natural_language_supported = OneSetField(accepted_fields=[NaturalLangField()], required=True,
                                                       default=['en'])
    ipp_versions_supported = OneSetField(accepted_fields=[KeywordField()], required=True, default=['1.1', '2.0'])
    ipp_features_supported = OneSetField(accepted_fields=[KeywordField()], default=['ipp-everywhere'])
    multiple_document_jobs_supported = BooleanField(default=False)
    multiple_operation_time_out = IntegerField(default=60)
    natural_language_configured = NaturalLangField(required=True, default='en')
    operations_supported = OneSetField(accepted_fields=[EnumField()], required=True, default=[
        OperationEnum.print_job,
        OperationEnum.validate_job,
        OperationEnum.create_job,
        OperationEnum.send_document,
        OperationEnum.cancel_job,
        OperationEnum.get_job_attributes,
        OperationEnum.get_printer_attributes,
        OperationEnum.get_jobs,
    ])
    pdl_override_supported = KeywordField(required=True, default='not-attempted')
    printer_info = TextWLField(default='KSI Gutenberg printer')
    printer_make_and_model = TextWLField(default='KSI Gutenberg')
    printer_location = TextWLField(default='Virtual')
    printer_more_info_manufacturer = UriField(default='https://github.com/KSIUJ/gutenberg')
    pages_per_minute_color = IntegerField(default=60)
    pages_per_minute = IntegerField(default=60)
    printer_current_time = DateTimeField(default=timezone.now())
    printer_is_accepting_jobs = BooleanField(required=True, default=True)
    printer_state_reasons = OneSetField(accepted_fields=[KeywordField()], required=True, default=['none'])
    printer_up_time = IntegerField(required=True, default=ipp_timestamp(timezone.now()))
    uri_authentication_supported = OneSetField(accepted_fields=[KeywordField()], required=True,
                                               default=['none'])
    uri_security_supported = OneSetField(accepted_fields=[KeywordField()], required=True, default=['tls'])
    device_service_count = IntegerField(default=1)
    print_color_mode_default = KeywordField(default='monochrome')
    print_color_mode_supported = OneSetField(accepted_fields=[KeywordField()], default=['monochrome', 'color', 'auto'])
    printer_get_attributes_supported = OneSetField(accepted_fields=[KeywordField()], default=['document-format'])

    # no default value
    printer_uri_supported = OneSetField(accepted_fields=[UriField()], required=True)
    printer_name = NameWLField(required=True)
    printer_more_info = UriField()
    printer_state = EnumField(required=True)
    printer_state_message = TextWLField()
    queued_job_count = IntegerField(required=True)
    printer_uuid = UriField(required=True)
    device_uuid = UriField(required=True)


class JobTemplatePrinterGroup(AttributeGroup):
    _tag = SectionEnum.printer
    _filter = 'job-template'

    # default
    copies_default = IntegerField(default=1)
    copies_supported = IntRangeField(default=IntRange(1, 99))
    sides_supported = OneSetField(accepted_fields=[KeywordField()],
                                  default=['one-sided', 'two-sided-long-edge', 'two-sided-short-edge'])
    sides_default = KeywordField(default='two-sided-long-edge')
    media_supported = OneSetField(accepted_fields=[KeywordField(), NameWLField()],
                                  default=[(KeywordField, 'iso_a4_210x297mm')])
    media_default = KeywordField(default='iso_a4_210x297mm')
    finishings_supported = OneSetField(accepted_fields=[EnumField()], default=[FinishingEnum.none])
    finishings_default = OneSetField(accepted_fields=[EnumField()], default=[FinishingEnum.none])
    orientation_requested_supported = OneSetField(accepted_fields=[EnumField()],
                                                  default=[PageOrientationEnum.portrait, PageOrientationEnum.landscape])
    orientation_requested_default = EnumField(default=PageOrientationEnum.portrait)
    output_bin_supported = OneSetField(accepted_fields=[KeywordField()], default='face-up')
    output_bin_default = KeywordField(default='face-up')
    print_quality_supported = OneSetField(accepted_fields=[EnumField()], default=[PrintQualityEnum.normal])
    print_quality_default = EnumField(default=PrintQualityEnum.normal)
    printer_resolution_supported = OneSetField(accepted_fields=[ResolutionField()],
                                               default=[Resolution(300, 300, Resolution.Units.DOTS_PER_INCH)])
    printer_resolution_default = ResolutionField(default=Resolution(300, 300, Resolution.Units.DOTS_PER_INCH))
    print_color_mode_supported = OneSetField(accepted_fields=[KeywordField()], default=['auto', 'color', 'monochrome'])
    print_color_mode_default = KeywordField(default='monochrome')


class PrinterAttributesGroup(MergedGroup):
    _tag = SectionEnum.printer
    merged_groups = [PrinterDescriptionGroup, JobTemplatePrinterGroup]


class GetJobsRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField(required=True)
    requesting_user_name = NameWLField()
    requested_attributes = OneSetField(accepted_fields=[KeywordField()])
    limit = IntegerField(default=10000)
    first_index = IntegerField(default=0)
    which_jobs = KeywordField(default='not-completed')
    my_jobs = BooleanField()


class PrintJobRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField(required=True)
    requesting_user_name = NameWLField()
    job_name = NameWLField()
    ipp_attribute_fidelity = BooleanField(default=False)
    document_name = NameWLField()
    compression = KeywordField(default='none')
    document_format = MimeTypeField()
    document_natural_language = NaturalLangField()
    job_k_octets = IntegerField()
    job_impressions = IntegerField()
    job_media_sheets = IntegerField()
    document_metadata = OneSetField(accepted_fields=[OctetStringField()])


class CreateJobRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField(required=True)
    requesting_user_name = NameWLField()
    job_name = NameWLField()
    ipp_attribute_fidelity = BooleanField(default=False)
    job_k_octets = IntegerField()
    job_impressions = IntegerField()
    job_media_sheets = IntegerField()


class SendDocumentRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField(required=True)
    job_id = IntegerField()
    job_uri = UriField()
    requesting_user_name = NameWLField()
    document_name = NameWLField()
    compression = KeywordField(default='none')
    document_format = MimeTypeField()
    document_natural_language = NaturalLangField()
    document_metadata = OneSetField(accepted_fields=[OctetStringField()])
    last_document = BooleanField(required=True)


class JobPrintResponseAttributes(AttributeGroup):
    _tag = SectionEnum.job

    job_state_reasons = OneSetField(accepted_fields=[KeywordField()], default=['none'])
    job_state_message = TextWLField(default='')

    job_uri = UriField(required=True)
    job_id = IntegerField(required=True)
    job_state = EnumField(required=True)


class JobTemplateAttributeGroup(AttributeGroup):
    _tag = SectionEnum.job
    _filter = 'job-template'

    # default
    copies = IntegerField(default=1)
    sides = KeywordField(default='two-sided-long-edge')
    media = KeywordField(default='iso_a4_210x297mm')
    finishings = OneSetField(accepted_fields=[EnumField()], default=[FinishingEnum.none])
    orientation_requested = EnumField(default=PageOrientationEnum.portrait)
    output_bin = KeywordField(default='face-up')
    print_quality = EnumField(default=PrintQualityEnum.normal)
    printer_resolution = ResolutionField(default=Resolution(300, 300, Resolution.Units.DOTS_PER_INCH))

    print_color_mode = KeywordField(default='auto')


class JobDescriptionAttributeGroup(AttributeGroup):
    _tag = SectionEnum.job
    _filter = 'job-description'

    job_state_reasons = OneSetField(accepted_fields=[KeywordField()], default=['none'])
    job_state_message = TextWLField(default='')

    job_uri = UriField(required=True)
    job_id = IntegerField(required=True)
    job_state = EnumField(required=True)
    job_printer_uri = UriField(required=True)
    job_name = NameWLField(required=True)
    job_more_info = UriField()
    job_originating_user_name = NameWLField(required=True)
    time_at_creation = IntegerField(required=True)
    time_at_processing = IntegerField(required=True)
    time_at_completed = IntegerField(required=True)
    job_printer_up_time = IntegerField(required=True)
    date_time_at_creation = DateTimeField()
    date_time_at_processing = DateTimeField()
    date_time_at_completed = DateTimeField()
    job_media_sheets = IntegerField()
    job_media_sheets_completed = IntegerField()


class JobObjectAttributeGroup(MergedGroup):
    _tag = SectionEnum.job
    merged_groups = [JobTemplateAttributeGroup, JobDescriptionAttributeGroup]
    _default_filter = ['job-id', 'job-uri']


class JobObjectAttributeGroupFull(MergedGroup):
    _tag = SectionEnum.job
    merged_groups = [JobTemplateAttributeGroup, JobDescriptionAttributeGroup]


class GetJobAttributesRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField()
    job_id = IntegerField()
    job_uri = UriField()
    requesting_user_name = NameWLField()
    requested_attributes = OneSetField(accepted_fields=[KeywordField()])


class CancelJobRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField()
    job_id = IntegerField()
    job_uri = UriField()
    message = TextWLField()
