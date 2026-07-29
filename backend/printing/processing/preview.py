import os
import shutil
import tempfile

from django.core.files import File

from control.models import JobArtefact, JobArtefactType
from printing.processing.converter import get_converter
from printing.processing.final_pages import FinalPageProcessor
from printing.processing.imposition import get_imposition_processor
from printing.processing.pages import PageSize, PageOrientation
from printing.utils import handle_cancellation
from control.models import OrientationRequested


def create_preview_for_artefact(job, artefact):
    """
    Creates intermediate PDF used as preview.
    """

    with tempfile.TemporaryDirectory() as artefact_tmpdir:

        file_path = artefact.file.path
        file_format = artefact.mime_type

        ext = os.path.splitext(file_path)[1].lower()

        if not ext:
            ext = '.bin'

        tmp_input = os.path.join(artefact_tmpdir, 'input' + ext)

        shutil.copyfile(file_path, tmp_input)

        converter = get_converter(file_format, artefact_tmpdir)

        preprocess_result = converter.preprocess(tmp_input)


        media_size = PageSize(width_mm=210, height_mm=297)

        final_page_processor = FinalPageProcessor(artefact_tmpdir, job.properties.n_up, media_size, preprocess_result.orientation, job.properties.fit_to_page)


        preview_path = converter.create_input_pdf(preprocess_result, final_page_processor.input_page_size)

        with open(preview_path, "rb") as file:

            preview = JobArtefact.objects.create(job=job, artefact_type=JobArtefactType.INTERMEDIATE, mime_type="application/pdf", document_number=artefact.document_number)

            preview.file.save(f"{artefact.document_number}_preview.pdf", File(file), save=True)


        return preview
