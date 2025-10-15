import logging
from time import sleep

from celery import shared_task
from celery.app.control import flatten_reply
from django.core.cache import cache

logger = logging.getLogger('gutenberg.main')

@shared_task
def update_supported_document_formats() -> dict:
    """
    Query all Celery workers for their supported document MIME types and filename extensions.
    Store the result in the Django cache.

    This function can be called directly or scheduled to run as a Celery task.
    """

    # Avoid a circular import
    from gutenberg.celery import app

    logger.debug("Refreshing supported document formats")
    # Let our own worker start responding when this task is scheduled from `gutenberg.celery.on_connect` before broadcasting
    sleep(1)
    # NOTE: This method always blocks for 3 seconds
    replies = app.control.broadcast("gutenberg_get_supported_formats", reply=True, timeout=3)
    replies = list(flatten_reply(replies).values())
    if len(replies) == 0:
        logger.warning("Got no replies from workers when refreshing supported document formats")
        supported_formats = { "mime_types": [], "extensions": [] }
    else:
        logger.debug(f"Received {len(replies)} replies from workers: {str(replies)}")

        # The `sorted` calls are used to keep the formats ordered in the order they appear in `CONVERTERS_LOCAL`.
        # This keeps related formats grouped together.
        #
        # All elements of the intersection must, by definition, also be present in the list in the first reply,
        # so the `.index(x)` call should not fail.
        #
        # The global supported formats are resolved as the intersection of all workers' supported formats
        # because the tasks might be executed by any worker.
        supported_formats = {
            "mime_types": sorted(
                set.intersection(*[set(reply["mime_types"]) for reply in replies]),
                key=lambda x: replies[0]["mime_types"].index(x),
            ),
            "extensions": sorted(
                set.intersection(*[set(reply["extensions"]) for reply in replies]),
                key=lambda x: replies[0]["extensions"].index(x),
            ),
        }
    cache.set("gutenberg_supported_formats", supported_formats, None)
    return supported_formats


def get_formats_supported_by_workers() -> dict:
    supported_formats = cache.get("gutenberg_supported_formats")
    if supported_formats is not None:
        return supported_formats

    try:
        logger.warning("Cache miss when getting supported document formats")
        return update_supported_document_formats()
    except Exception as e:
        logger.error(f"Failed to refresh supported document formats: {str(e)}", exc_info=True)
        return { "mime_types": [], "extensions": [] }
