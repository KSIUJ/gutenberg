import os
import subprocess
from abc import ABC, abstractmethod
from typing import List

from pypdf import PdfReader, PdfWriter, Transformation, PageObject

from printing.processing.pages import PageSize, PageSizes, PageOrientation
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S


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
    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> str:
        """
        Creates the output PDF with imposition applied, and Final Pages rotated to exactly
        match the media size without rotating.

        :return: The path to the output PDF
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

    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> str:
        if final_page_orientation == PageOrientation.PORTRAIT:
            # No-op, the orientation of the Final Pages is already portrait
            return final_pages_file

        # The Final Pages are in landscape orientation, rotate them 90
        out = os.path.join(self.work_dir, 'output.pdf')
        self.run_in_sandbox([
            "pdftk", final_pages_file, "cat", "1-endeast", "output", out,
        ])
        return out


class BookletImpositionProcessor(SandboxImpositionProcessor):
    def get_final_page_sizes(self) -> PageSizes:
        landscape_size = PageSize(width_mm=self.media_size.width_mm, height_mm=self.media_size.height_mm/2)
        return PageSizes(
            portrait=landscape_size.rotated(),
            landscape=landscape_size,
        )

    def create_output_pdf(self, final_pages_file: str, final_page_orientation: PageOrientation) -> str:
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
            page.rotate(rotation)

        media_sheet_count = -(len(reader.pages) // -4) # Ceil division
        for i in range(media_sheet_count):
            front_page = writer.add_blank_page(width=self.media_size.width_pt(), height=self.media_size.height_pt())
            try_add_page(2 * media_sheet_count - 1 - 2*i, front_page, True)
            try_add_page(2 * media_sheet_count + 2*i, front_page, False)

            rear_page = writer.add_blank_page(width=self.media_size.width_pt(), height=self.media_size.height_pt())
            try_add_page(2 * media_sheet_count - 2 - 2*i, rear_page, False)
            try_add_page(2 * media_sheet_count + 1 + 2*i, rear_page, True)

        with open(out, "xb") as output_file:
            writer.write(output_file)
        return out


def get_imposition_processor(imposition_template: str, media_size: PageSize, work_dir: str) -> BaseImpositionProcessor:
    if imposition_template == "none":
        return StandardImpositionProcessor(media_size, work_dir)
    if imposition_template == "booklet":
        return BookletImpositionProcessor(media_size, work_dir)
    raise ValueError(f"Unknown imposition template: {imposition_template}")
