from django.utils import timezone

from ipp import SUPPORTED_IPP_FORMATS, DEFAULT_IPP_FORMAT
from ipp.constants import SectionEnum, OperationEnum, FinishingEnum, PageOrientationEnum, PrintQualityEnum
from ipp.fields import MimeTypeField, UriField, CharsetField, OneSetField, BooleanField, KeywordField, NaturalLangField, \
    IntegerField, EnumField, TextWLField, DateTimeField, NameWLField, IntRangeField, IntRange, ResolutionField, \
    Resolution, OctetStringField, UnknownField, Collection, CollectionField, UnionField
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
    multiple_operation_time_out = IntegerField(default=600)
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
        OperationEnum.close_job,
        OperationEnum.cancel_my_jobs,
        OperationEnum.identify_printer,
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
    uri_security_supported = OneSetField(accepted_fields=[KeywordField()], required=True, default=['none'])
    device_service_count = IntegerField(default=1)
    print_color_mode_default = KeywordField(default='monochrome')
    print_color_mode_supported = OneSetField(accepted_fields=[KeywordField()], default=['monochrome', 'color', 'auto'])
    printer_get_attributes_supported = OneSetField(accepted_fields=[KeywordField()], default=['document-format'])
    which_jobs_supported = OneSetField(accepted_fields=[KeywordField()], default=['all', 'completed', 'not-completed'])
    identify_actions_supported = OneSetField(accepted_fields=[KeywordField()], default=['flash'])
    identify_actions_default = KeywordField(default='flash')

    printer_geo_location = UnknownField(default=True)
    printer_organization = OneSetField(accepted_fields=[TextWLField()], default=[''])
    printer_organizational_unit = OneSetField(accepted_fields=[TextWLField()], default=[''])
    printer_device_id = TextWLField(default='MFG:KSI;MDL:gutenberg')
    job_ids_supported = BooleanField(default=True)
    job_creation_attributes_supported = OneSetField(accepted_fields=[KeywordField()],
                                                    default=['copies', 'sides', 'media', 'finishings',
                                                             'orientation-requested', 'output-bin', 'print-quality',
                                                             'printer-resolution', 'print-color-mode',
                                                             'document-format', 'document-metadata', 'document-name',
                                                             'document-natural-language', 'ipp-attribute-fidelity',
                                                             'job-name', 'print-rendering-intent',
                                                             'print-content-optimize', 'page_ranges'])
    preferred_attributes_supported = BooleanField(default=False)
    multiple_operation_time_out_action = KeywordField(default='process-job')
    overrides_supported = OneSetField(accepted_fields=[KeywordField()], default=['pages', 'document-number'])
    printer_supply = OneSetField(accepted_fields=[OctetStringField()], default=[
        b'index=1;class=supplyThatIsConsumed;type=toner;unit=percent;maxcapacity=100;level=100;colorantname=multi-color;'])
    printer_supply_description = OneSetField(accepted_fields=[TextWLField()], default=['Virtual Toner'])
    printer_state_change_date_time = DateTimeField(default=timezone.now())
    printer_state_change_time = IntegerField(default=ipp_timestamp(timezone.now()))
    printer_config_change_date_time = DateTimeField(default=timezone.now())
    printer_config_change_time = IntegerField(default=ipp_timestamp(timezone.now()))

    # no default value
    printer_uri_supported = OneSetField(accepted_fields=[UriField()], required=True)
    printer_name = NameWLField(required=True)
    printer_more_info = UriField()
    printer_state = EnumField(required=True)
    printer_state_message = TextWLField()

    # no default and required by standard
    printer_supply_info_uri = UriField()
    queued_job_count = IntegerField()
    printer_uuid = UriField()
    device_uuid = UriField()
    printer_icons = OneSetField(accepted_fields=[UriField()])


class MediaSizeCollection(Collection):
    x_dimension = IntegerField(required=True)
    y_dimension = IntegerField(required=True)


class MediaCollection(Collection):
    media_key = UnionField(accepted_fields=[KeywordField(), NameWLField()])
    media_bottom_margin = IntegerField()
    media_top_margin = IntegerField()
    media_left_margin = IntegerField()
    media_right_margin = IntegerField()
    media_size = CollectionField(collection_type=MediaSizeCollection)
    media_size_name = UnionField(accepted_fields=[KeywordField(), NameWLField()])
    media_source = UnionField(accepted_fields=[KeywordField(), NameWLField()])
    media_type = UnionField(accepted_fields=[KeywordField(), NameWLField()])


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
    media_ready = OneSetField(accepted_fields=[KeywordField(), NameWLField()],
                              default=[(KeywordField, 'iso_a4_210x297mm')])
    media_default = KeywordField(default='iso_a4_210x297mm')
    finishings_supported = OneSetField(accepted_fields=[EnumField()], default=[FinishingEnum.none])
    finishings_default = OneSetField(accepted_fields=[EnumField()], default=[FinishingEnum.none])
    orientation_requested_supported = OneSetField(accepted_fields=[EnumField()],
                                                  default=[PageOrientationEnum.portrait, PageOrientationEnum.landscape])
    orientation_requested_default = EnumField(default=PageOrientationEnum.portrait)
    output_bin_supported = OneSetField(accepted_fields=[KeywordField()], default=['face-up'])
    output_bin_default = KeywordField(default='face-up')
    print_quality_supported = OneSetField(accepted_fields=[EnumField()], default=[PrintQualityEnum.normal])
    print_quality_default = EnumField(default=PrintQualityEnum.normal)
    printer_resolution_supported = OneSetField(accepted_fields=[ResolutionField()],
                                               default=[Resolution(150, 150, Resolution.Units.DOTS_PER_INCH),
                                                        Resolution(300, 300, Resolution.Units.DOTS_PER_INCH),
                                                        Resolution(600, 600, Resolution.Units.DOTS_PER_INCH)])
    printer_resolution_default = ResolutionField(default=Resolution(300, 300, Resolution.Units.DOTS_PER_INCH))
    print_color_mode_supported = OneSetField(accepted_fields=[KeywordField()], default=['auto', 'color', 'monochrome'])
    print_color_mode_default = KeywordField(default='monochrome')
    pwg_raster_document_resolution_supported = printer_resolution_supported
    pwg_raster_document_type_supported = OneSetField(accepted_fields=[KeywordField()],
                                                     default=['black_1', 'sgray_8', 'srgb_8'])
    pwg_raster_document_sheet_back = OneSetField(accepted_fields=[KeywordField()], default=['normal'])
    print_rendering_intent_supported = OneSetField(accepted_fields=[KeywordField()], default=['auto'])
    print_rendering_intent_default = KeywordField(default='auto')
    print_content_optimize_supported = OneSetField(accepted_fields=[KeywordField()], default=['auto'])
    print_content_optimize_default = KeywordField(default='auto')
    page_ranges_supported = BooleanField(default=True)
    media_type_supported = OneSetField(accepted_fields=[KeywordField()], default=['stationery'])
    media_source_supported = OneSetField(accepted_fields=[KeywordField()], default=['main'])
    media_size_supported = OneSetField(accepted_fields=[CollectionField(collection_type=MediaSizeCollection)],
                                       default=[MediaSizeCollection(x_dimension=21000, y_dimension=29700)])
    media_col_database = OneSetField(accepted_fields=[CollectionField(collection_type=MediaCollection)],
                                     default=[MediaCollection(
                                         media_key='iso_a4_210x297mm',
                                         media_bottom_margin=635,
                                         media_top_margin=635,
                                         media_left_margin=340,
                                         media_right_margin=340,
                                         media_size=MediaSizeCollection(x_dimension=21000, y_dimension=29700),
                                         media_size_name='iso_a4_210x297mm',
                                         media_source='main',
                                         media_type='stationery'
                                     )])
    media_col_ready = media_col_database
    media_bottom_margin_supported = IntegerField(default=635)
    media_top_margin_supported = IntegerField(default=635)
    media_left_margin_supported = IntegerField(default=340)
    media_right_margin_supported = IntegerField(default=340)


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
    print_rendering_intent = KeywordField(default='auto')
    print_color_mode = KeywordField(default='auto')
    print_content_optimize = KeywordField(default='auto')
    page_ranges = OneSetField(accepted_fields=[IntRangeField()])
    media_type = KeywordField()
    media_source = KeywordField()
    media_size = CollectionField(collection_type=MediaSizeCollection)
    media_col = CollectionField(collection_type=MediaCollection)
    media_bottom_margin = IntegerField(default=635)
    media_top_margin = IntegerField(default=635)
    media_left_margin = IntegerField(default=340)
    media_right_margin = IntegerField(default=340)


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


class CancelMyJobsRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField()
    job_ids = OneSetField(accepted_fields=[IntegerField()])
    requesting_user_name = NameWLField()
    message = TextWLField()


class CloseJobRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField()
    job_id = IntegerField()
    job_uri = UriField()
    requesting_user_name = NameWLField()


class IdentifyPrinterRequestOperationGroup(BaseOperationGroup):
    printer_uri = UriField()
    requesting_user_name = NameWLField()
    identify_actions = OneSetField(accepted_fields=[KeywordField()])
