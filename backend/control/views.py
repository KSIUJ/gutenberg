from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import logging

from control.models import Printer
from printing.services import trigger_test_print_from_file, find_test_pdf_from_static

logger = logging.getLogger('gutenberg.admin.test_print')


@staff_member_required
@require_POST
def trigger_test_print_view(request, printer_id):
    """
    Triggers a test print for the selected printer.
    Returns a JSON response with status 'ok' and ID of the job if it succeeds
    or status 'error' if it fails .
    """
    logger.info(
        "trigger_test_print_view called: method=%s referer=%s remote_addr=%s user=%s",
        request.method,
        request.META.get('HTTP_REFERER'),
        request.META.get('REMOTE_ADDR'),
        getattr(request.user, 'username', '<anon>'))

    printer = get_object_or_404(Printer, pk=printer_id)
    pdf_path = find_test_pdf_from_static('documents/test_page.pdf')

    if not pdf_path:
        messages.error(request,
                       "Test PDF file 'documents/test_page.pdf' was not found in static assets.")
        return JsonResponse({"status": "error", "message": "PDF not found"}, status=404)

    try:
        job = trigger_test_print_from_file(printer=printer, user=request.user,
                                           file_path=pdf_path, color=False,
                                           duplex=False)
        messages.success(request,
                         f"Test print job #{job.id} dispatched to '{printer.name}'.")
    except ValidationError as e:
        msgs = getattr(e, 'messages', [str(e)])
        messages.error(request, "; ".join(msgs))
        return JsonResponse({"status": "error", "message": "Validation failed"},
                            status=400)
    except Exception as e:
        logger.exception("Error while triggering test print for printer %s: %s",
                         printer_id, e)
        messages.error(request, f"Error triggering test print: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "ok", "job_id": job.id})
