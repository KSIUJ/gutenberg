import os
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from pypdf import PdfReader, PdfWriter, Transformation, PageObject

from printing.processing.pages import PageSize, PageSizes, PageOrientation
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S, ceil_div


@dataclass(frozen=True)
class ImpositionResult:
    output_file: str
    media_sheet_count: int
    media_sheet_page_count: int


class BaseImpositionProcessor(ABC):
    media_size: PageSize

    def __init__(self, media_size: PageSize):
        if media_size.is_horizontal():
            raise ValueError("BaseImpositionTemplate expects a vertical media size")
        self.media_size = media_size

    @abstractmethod
    def get_final_page_sizes(self) -> PageSizes:
        """
        Returns the size of the Final Pages for the landscape and portrait orientations
        for printing on Media Sheets of the size `media_size`.
        """

        pass

    @abstractmethod
    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> ImpositionResult:
        """
        Creates the output PDF with imposition applied, and Final Pages rotated to exactly
        match the media size without rotating.
        """

        pass

class SandboxImpositionProcessor(BaseImpositionProcessor, ABC):
    work_dir: str

    def __init__(self, media_size: PageSize, work_dir: str):
        super().__init__(media_size)
        self.work_dir = work_dir

    def run_in_sandbox(self, command: List[str]) -> str:
        sandboxed_command = [SANDBOX_PATH, self.work_dir] + command
        return subprocess.check_output(
            sandboxed_command,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
        )


class StandardImpositionProcessor(SandboxImpositionProcessor):
    def get_final_page_sizes(self) -> PageSizes:
        return PageSizes(
            portrait=self.media_size,
            landscape=self.media_size.rotated(),
        )

    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> ImpositionResult:
        out = os.path.join(self.work_dir, 'output.pdf')
        reader = PdfReader(final_pages_file)
        writer = PdfWriter()

        rotation = 0 if final_page_orientation == PageOrientation.PORTRAIT else 90

        for page in reader.pages:
            dest_page = writer.add_blank_page(width=self.media_size.width_pt(), height=self.media_size.height_pt())
            page = page.rotate(rotation)
            page.transfer_rotation_to_content()
            dest_page.merge_page(page)

        # TODO: Add extra blank page if the number of pages is odd and duplex printing is enabled

        with open(out, "xb") as output_file:
            writer.write(output_file)
        return ImpositionResult(
            output_file=out,
            media_sheet_count=ceil_div(len(reader.pages), 2),
            media_sheet_page_count=len(reader.pages),
        )


class BookletImpositionProcessor(SandboxImpositionProcessor):
    def get_final_page_sizes(self) -> PageSizes:
        landscape_size = PageSize(width_mm=self.media_size.width_mm, height_mm=self.media_size.height_mm/2)
        return PageSizes(
            portrait=landscape_size.rotated(),
            landscape=landscape_size,
        )

    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> ImpositionResult:
        out = os.path.join(self.work_dir, 'output.pdf')
        reader = PdfReader(final_pages_file)
        writer = PdfWriter()

        y_midpoint_pt = self.media_size.height_pt()/2
        rotation = 90 if final_page_orientation == PageOrientation.PORTRAIT else 0

        def try_add_page(source_index: int, target: PageObject, top = False):
            if source_index < 0 or source_index >= len(reader.pages):
                return
            # Note: This modifies the `PageObject` instance
            page = reader.pages[source_index].rotate(rotation)
            page.transfer_rotation_to_content()
            transformation = Transformation()
            if top:
                transformation = transformation.translate(0, y_midpoint_pt)
            target.merge_transformed_page(page, transformation)

        media_sheet_count = ceil_div(len(reader.pages), 4)
        for i in range(media_sheet_count):
            front_page = writer.add_blank_page(width=self.media_size.width_pt(), height=self.media_size.height_pt())
            try_add_page(2 * media_sheet_count - 1 - 2*i, front_page, True)
            try_add_page(2 * media_sheet_count + 2*i, front_page, False)

            rear_page = writer.add_blank_page(width=self.media_size.width_pt(), height=self.media_size.height_pt())
            try_add_page(2 * media_sheet_count - 2 - 2*i, rear_page, False)
            try_add_page(2 * media_sheet_count + 1 + 2*i, rear_page, True)

        with open(out, "xb") as output_file:
            writer.write(output_file)
        return ImpositionResult(
            output_file=out,
            media_sheet_count=media_sheet_count,
            media_sheet_page_count=2*media_sheet_count,
        )


def get_imposition_processor(imposition_template: str, media_size: PageSize, work_dir: str) -> BaseImpositionProcessor:
    if imposition_template == "none":
        return StandardImpositionProcessor(media_size, work_dir)
    if imposition_template == "booklet":
        return BookletImpositionProcessor(media_size, work_dir)
    raise ValueError(f"Unknown imposition template: {imposition_template}")
