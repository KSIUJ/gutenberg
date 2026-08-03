import os
import subprocess
import tempfile

from celery import shared_task
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from control.models import (
    PreviewStatus,
    PrintPreview,
    PrintPreviewPage,
)
from printing.processing.job import create_output_pdfs
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S


# Preview image density in dots per inch,
# see https://imagemagick.org/command-line-options/#density
# Raster previews are rendered at browser-like screen density.
PREVIEW_DENSITY = 96
# JPEG compression quality of the preview images
PREVIEW_QUALITY = 75


class ObsoletePreview(Exception):
    pass


def _ensure_preview_is_current(
    preview_id: int,
    expected_generation: int,
) -> PrintPreview:
    preview = PrintPreview.objects.select_related('job').get(
        id=preview_id,
    )

    if preview.generation != expected_generation:
        raise ObsoletePreview()

    if preview.status == PreviewStatus.CANCELED:
        raise ObsoletePreview()

    if (
        preview.configuration_version
        != preview.job.configuration_version
    ):
        raise ObsoletePreview()

    return preview


def _rasterize_pdf(
    pdf_path: str,
    output_directory: str,
    prefix: str,
) -> list[str]:
    output_pattern = os.path.join(
        output_directory,
        f'{prefix}-%04d.jpg',
    )

    _run_in_sandbox(
        output_directory,
        [
            'magick',
            '-density',
            str(PREVIEW_DENSITY),
            pdf_path,
            '-background',
            'white',
            '-alpha',
            'remove',
            '-quality',
            str(PREVIEW_QUALITY),
            output_pattern,
        ],
    )

    filenames = [
        os.path.join(output_directory, filename)
        for filename in os.listdir(output_directory)
        if filename.startswith(prefix) and filename.endswith('.jpg')
    ]
    return sorted(filenames)


def _run_in_sandbox(work_dir: str, command: list[str]) -> str:
    return subprocess.check_output(
        [SANDBOX_PATH, work_dir, *command],
        text=True,
        stderr=subprocess.STDOUT,
        timeout=TASK_TIMEOUT_S,
    )


def _get_image_dimensions(image_path: str) -> tuple[int, int]:
    """
    Return the displayed image size in pixels as ``(width, height)``.

    ``magick identify -auto-orient`` applies the EXIF orientation tag before
    measuring, so portrait images stored sideways are reported in their
    displayed orientation.
    """
    result = _run_in_sandbox(
        os.path.dirname(image_path),
        [
            'magick',
            'identify',
            '-auto-orient',
            '-format',
            '%w %h',
            image_path,
        ],
    )

    width, height = result.strip().split()
    return int(width), int(height)


@shared_task(bind=True)
def generate_preview(
    self,
    preview_id: int,
    expected_generation: int,
):
    try:
        preview = _ensure_preview_is_current(
            preview_id,
            expected_generation,
        )

        preview.status = PreviewStatus.PROCESSING
        preview.error = ''
        preview.celery_task_id = self.request.id or ''
        preview.save(
            update_fields=[
                'status',
                'error',
                'celery_task_id',
                'updated_at',
            ]
        )

        with tempfile.TemporaryDirectory() as work_dir:
            processed_documents = create_output_pdfs(
                preview.job,
                work_dir,
            )

            generated_pages = []
            page_number = 1

            for document_index, document in enumerate(
                processed_documents
            ):
                image_paths = _rasterize_pdf(
                    document.output_file,
                    work_dir,
                    f'document-{document_index:03}',
                )

                for image_path in image_paths:
                    width, height = _get_image_dimensions(image_path)

                    generated_pages.append(
                        (
                            page_number,
                            image_path,
                            width,
                            height,
                        )
                    )
                    page_number += 1

            _ensure_preview_is_current(
                preview_id,
                expected_generation,
            )

            with transaction.atomic():
                locked_preview = (
                    PrintPreview.objects
                    .select_for_update()
                    .select_related('job')
                    .get(id=preview_id)
                )

                if (
                    locked_preview.generation
                    != expected_generation
                    or locked_preview.status
                    == PreviewStatus.CANCELED
                    or locked_preview.configuration_version
                    != locked_preview.job.configuration_version
                ):
                    raise ObsoletePreview()

                # File cleanup is handled by the model-level post_delete signal.
                locked_preview.pages.all().delete()

                for (
                        number,
                        image_path,
                        width,
                        height,
                ) in generated_pages:
                    page = PrintPreviewPage(
                        preview=locked_preview,
                        number=number,
                        width=width,
                        height=height,
                    )

                    with open(image_path, 'rb') as image_file:
                        page.image.save(
                            f'job-{locked_preview.job_id}-'
                            f'generation-{expected_generation}-'
                            f'page-{number:04}.jpg',
                            File(image_file),
                            save=False,
                        )

                    page.save()

                locked_preview.status = PreviewStatus.READY
                locked_preview.error = ''
                locked_preview.save(
                    update_fields=[
                        'status',
                        'error',
                        'updated_at',
                    ]
                )

    except ObsoletePreview:
        return

    except Exception as exception:
        updated = PrintPreview.objects.filter(
            id=preview_id,
            generation=expected_generation,
        ).exclude(
            status=PreviewStatus.CANCELED,
        ).update(
            status=PreviewStatus.FAILED,
            error=str(exception),
            updated_at=timezone.now(),
        )

        if updated:
            raise
