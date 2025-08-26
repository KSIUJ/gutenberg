from enum import IntEnum


class SectionEnum(IntEnum):
    SECTIONS = 0x00
    SECTIONS_MASK = 0xf0
    operation = 0x01
    job = 0x02
    END = 0x03
    printer = 0x04
    unsupported = 0x05

    @classmethod
    def is_section_tag(cls, tag):
        return (tag & cls.SECTIONS_MASK) == cls.SECTIONS


class TagEnum(IntEnum):
    unsupported_value = 0x10
    unknown_value = 0x12
    no_value = 0x13
    integer = 0x21
    boolean = 0x22
    enum = 0x23
    octet_str = 0x30
    datetime = 0x31
    resolution = 0x32
    range_of_integer = 0x33
    begin_collection = 0x34
    text_with_language = 0x35
    name_with_language = 0x36
    end_collection = 0x37
    text_without_language = 0x41
    name_without_language = 0x42
    keyword = 0x44
    uri = 0x45
    uri_scheme = 0x46
    charset = 0x47
    natural_language = 0x48
    mime_media_type = 0x49
    member_attr_name = 0x4a


class StatusCodeEnum(IntEnum):
    ok = 0x0000
    successful_ok_ignored_or_substituted_attributes = 0x0001
    successful_ok_conflicting_attributes = 0x0002

    client_error_bad_request = 0x0400
    client_error_forbidden = 0x0401
    client_error_not_authenticated = 0x0402
    client_error_not_authorized = 0x0403
    client_error_not_possible = 0x0404
    client_error_timeout = 0x0405
    client_error_not_found = 0x0406
    client_error_gone = 0x0407
    client_error_request_entity_too_large = 0x0408
    client_error_request_value_too_long = 0x0409
    client_error_document_format_not_supported = 0x040a
    client_error_attributes_or_values_not_supported = 0x040b
    client_error_uri_scheme_not_supported = 0x040c
    client_error_charset_not_supported = 0x040d
    client_error_conflicting_attributes = 0x040e
    client_error_compression_not_supported = 0x040f
    client_error_compression_error = 0x0410
    client_error_document_format_error = 0x0411
    client_error_document_access_error = 0x0412

    server_error_internal_error = 0x0500
    server_error_operation_not_supported = 0x0501
    server_error_service_unavailable = 0x0502
    server_error_version_not_supported = 0x0503
    server_error_device_error = 0x0504
    server_error_temporary_error = 0x0505
    server_error_not_accepting_jobs = 0x0506
    server_error_busy = 0x0507
    server_error_job_canceled = 0x508
    server_error_multiple_document_jobs_not_supported = 0x0509


class OperationEnum(IntEnum):
    print_job = 0x0002
    validate_job = 0x0004
    create_job = 0x0005
    send_document = 0x0006
    cancel_job = 0x0008
    get_job_attributes = 0x0009
    get_jobs = 0x000a
    get_printer_attributes = 0x000b
    cancel_my_jobs = 0x0039
    close_job = 0x003B
    identify_printer = 0x003C

    cups_get_default = 0x4001
    cups_list_all_printers = 0x4002


class JobStateEnum(IntEnum):
    pending = 3
    pending_held = 4
    processing = 5
    processing_stopped = 6
    canceled = 7
    aborted = 8
    completed = 9


class PrinterStateEnum(IntEnum):
    idle = 3
    processing = 4
    stopped = 5


class FinishingEnum(IntEnum):
    none = 3
    staple = 4
    punch = 5
    cover = 6
    bind = 7
    saddle_stitch = 8
    edge_stitch = 9
    staple_top_left = 20
    staple_bottom_left = 21
    staple_top_right = 22
    staple_bottom_right = 23
    edge_stitch_left = 24
    edge_stitch_top = 25
    edge_stitch_right = 26
    edge_stitch_bottom = 27
    staple_dual_left = 28
    staple_dual_top = 29
    staple_dual_right = 30
    staple_dual_bottom = 31


class PageOrientationEnum(IntEnum):
    portrait = 3
    landscape = 4
    reverse_landscape = 5
    reverse_portrait = 6


class PrintQualityEnum(IntEnum):
    draft = 3
    normal = 4
    high = 5


class ValueTagsEnum(IntEnum):
    unsupported = 0x10
    unknown = 0x12
    no_value = 0x13
