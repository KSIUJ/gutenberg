import os
import shutil
import tempfile
from dataclasses import dataclass

from control.models import (
    JobArtefactType,
    OrientationRequested,
    TwoSidedPrinting,
)
from printing.processing.converter import get_converter
from printing.processing.final_pages import (
    FinalPageProcessor,
    NoPagesToPrintException,
)
from printing.processing.imposition import get_imposition_processor
from printing.processing.pages import PageOrientation, PageSize
from printing.utils import handle_cancellation


@dataclass(frozen=True)
class ProcessedDocument:
    output_file: str
    media_sheet_page_count: int


def create_output_pdfs(job, work_dir: str) -> list[ProcessedDocument]:
    results = []

    artefacts = job.artefacts.filter(
        artefact_type=JobArtefactType.SOURCE,
    ).order_by('document_number')

    for index, artefact in enumerate(artefacts):
        artefact_work_dir = tempfile.mkdtemp(
            prefix=f'artefact-{index:03}-',
            dir=work_dir,
        )

        file_path = artefact.file.path
        extension = os.path.splitext(file_path)[1].lower() or '.bin'
        temporary_input = os.path.join(
            artefact_work_dir,
            'input' + extension,
        )
        shutil.copyfile(file_path, temporary_input)

        converter = get_converter(
            artefact.mime_type,
            artefact_work_dir,
        )
        preprocess_result = converter.preprocess(temporary_input)
        handle_cancellation(job)

        # TODO: Replace this with the selected printer media size.
        media_size = PageSize(width_mm=210, height_mm=297)

        imposition_processor = get_imposition_processor(
            job.properties.imposition_template,
            media_size,
            artefact_work_dir,
        )

        input_orientation = {
            OrientationRequested.AUTO: preprocess_result.orientation,
            OrientationRequested.LANDSCAPE: PageOrientation.LANDSCAPE,
            OrientationRequested.PORTRAIT: PageOrientation.PORTRAIT,
        }[job.properties.orientation_requested]

        final_page_processor = FinalPageProcessor(
            artefact_work_dir,
            job.properties.n_up,
            imposition_processor.get_final_page_sizes(),
            input_orientation,
            job.properties.fit_to_page,
        )

        input_pdf = converter.create_input_pdf(
            preprocess_result,
            final_page_processor.input_page_size,
        )
        handle_cancellation(job)

        final_pages_pdf = final_page_processor.create_final_pages(
            input_pdf,
            job.properties.pages_to_print,
        )
        handle_cancellation(job)

        imposition_result = imposition_processor.create_output_pdf(
            final_pages_pdf,
            final_page_processor.final_page_orientation,
            job.properties.two_sides != TwoSidedPrinting.ONE_SIDED,
        )

        output_file = os.path.join(
            work_dir,
            f'{index:03}_output.pdf',
        )
        shutil.copyfile(
            imposition_result.output_file,
            output_file,
        )

        results.append(
            ProcessedDocument(
                output_file=output_file,
                media_sheet_page_count=(
                    imposition_result.media_sheet_page_count
                ),
            )
        )

        handle_cancellation(job)

    if not results:
        raise NoPagesToPrintException()

    return results
