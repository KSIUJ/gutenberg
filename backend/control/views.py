from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
import logging
import json

from control.models import Printer
from printing.services import trigger_test_print_from_file, find_test_pdf_from_static

logger = logging.getLogger('gutenberg.admin.test_print')


@staff_member_required
@require_POST
def trigger_test_print_view(request, printer_id):
    """
    Triggers a test print for the selected printer.
    Accepts JSON body with 'color' (bool) and 'duplex' (bool) parameters.
    Returns a JSON response with status 'ok' and ID of the job if it succeeds
    or status 'error' if it fails .
    """
    logger.info(
        "trigger_test_print_view called: method=%s referer=%s remote_addr=%s user=%s",
        request.method,
        request.META.get('HTTP_REFERER'),
        request.META.get('REMOTE_ADDR'),
        getattr(request.user, 'username', '<anon>'))
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in request body from user %s",
                       getattr(request.user, 'username', '<anon>'))
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400
        )

    color = data.get('color', False)
    duplex = data.get('duplex', False)

    if not isinstance(color, bool) or not isinstance(duplex, bool):
        logger.warning(
            "Invalid parameter types: color=%s (type %s), duplex=%s (type %s)",
            color, type(color).__name__, duplex, type(duplex).__name__)
        return JsonResponse(
            {"status": "error",
             "message": "Parameters 'color' and 'duplex' must be boolean"},
            status=400
        )

    logger.info("Test print requested: color=%s, duplex=%s, printer_id=%s",
                color, duplex, printer_id)

    printer = get_object_or_404(Printer, pk=printer_id)
    pdf_filename = 'documents/test_page_colored.pdf' if color else 'documents/test_page_grayscale.pdf'
    pdf_path = find_test_pdf_from_static(pdf_filename)

    if not pdf_path:
        messages.error(request,
                       f"Test PDF file '{pdf_filename}' was not found in static assets.")
        return JsonResponse({"status": "error", "message": "PDF not found"}, status=404)

    try:
        job = trigger_test_print_from_file(
            printer=printer,
            user=request.user,
            file_path=pdf_path,
            color=color,
            duplex=duplex
        )
        msg = f"Test print job #{job.id} (color={color}, duplex={duplex}) dispatched to '{printer.name}'."
        messages.success(request, msg)
        logger.info(msg)
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
