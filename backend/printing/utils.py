import logging
import os
from typing import Optional, Callable

from control.models import GutenbergJob, JobStatus

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_PATH = os.path.join(BASE_DIR, 'sandbox.sh')
TASK_TIMEOUT_S = 15 * 60
PRINTING_TIMEOUT_S = 10 * 60

AUTODETECT_IPP_FORMAT = 'application/octet-stream'
DEFAULT_IPP_FORMAT = AUTODETECT_IPP_FORMAT
SUPPORTED_IPP_FORMATS = ['application/pdf', 'image/pwg-raster', 'image/jpeg', 'application/postscript',
                         AUTODETECT_IPP_FORMAT]

MM_PER_PT = 25.4 / 72

logger = logging.getLogger('gutenberg.worker')


class JobCanceledException(ValueError):
    pass


class DocumentFormatError(ValueError):
    pass


def handle_cancellation(job: GutenbergJob, handler: Optional[Callable[[], None]] = None):
    # We allow a low possibility of a race condition here as the impact would be negligible
    # (ie. ignored request) and the probability is low.
    job.refresh_from_db()
    if job.status == JobStatus.CANCELING:
        logger.info("Canceling job {}".format(job))
        if handler:
            handler()
        job.status = JobStatus.CANCELED
        job.status_reason = 'Canceled by user'
        job.save()
        raise JobCanceledException()
