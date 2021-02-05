import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_PATH = os.path.join(BASE_DIR, 'sandbox.sh')
TASK_TIMEOUT_S = 15 * 60
PRINTING_TIMEOUT_S = 10 * 60

AUTODETECT_IPP_FORMAT = 'application/octet-stream'
DEFAULT_IPP_FORMAT = AUTODETECT_IPP_FORMAT
SUPPORTED_IPP_FORMATS = ['application/pdf', 'image/pwg-raster', 'image/jpeg', 'application/postscript',
                         AUTODETECT_IPP_FORMAT]


class JobCanceledException(ValueError):
    pass


class DocumentFormatError(ValueError):
    pass
