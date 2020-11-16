from ipp.constants import StatusCodeEnum


class IppError(ValueError):
    def error_code(self):
        return StatusCodeEnum.client_error_bad_request


class BadRequestError(IppError):
    def error_code(self):
        return StatusCodeEnum.client_error_bad_request


class InvalidTagError(BadRequestError):
    pass


class MissingFieldError(BadRequestError):
    pass


class FieldOrderError(BadRequestError):
    pass


class InvalidCharsetError(IppError):
    def error_code(self):
        return StatusCodeEnum.client_error_charset_not_supported


class UnsupportedIppVersionError(IppError):
    def error_code(self):
        return StatusCodeEnum.server_error_version_not_supported


class BadRequestIDError(BadRequestError):
    pass


class InvalidGroupError(BadRequestError):
    pass


class DocumentFormatError(IppError):
    def error_code(self):
        return StatusCodeEnum.client_error_document_format_not_supported
