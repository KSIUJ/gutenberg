import os
import subprocess
from itertools import chain
from math import log2
from typing import List, Optional

from pypdf import PdfReader, PdfWriter, Transformation

from printing.processing.pages import PageSize, PageSizes, PageOrientation
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S


class NoPagesToPrintException(BaseException):
    def __init__(self):
        super().__init__("No pages to print")


class FinalPageProcessor:
    """
    A utility for creating Final Pages from Input Pages by applying page filter and n-up.

    Finds the Input Page size based on the n-up and Input Page orientation settings and the Final Page sizes
    for the selected imposition template.

    Input Page orientation is not necessarily the orientation of the pages in the input file (e.g., PDF).
    The pages from the input file will be positioned on the Input Pages without rotating it.
    """

    work_dir: str
    final_page_orientation: PageOrientation
    final_page_size: PageSize
    input_page_size: PageSize
    rows: int
    columns: int

    def __init__(self, work_dir: str, n: int, final_sizes: PageSizes, input_orientation: PageOrientation):
        self.work_dir = work_dir

        divide_count = round(log2(n))
        if 2 ** divide_count != n:
            raise ValueError("n must be a power of 2")

        self.final_page_orientation = input_orientation.rotate() if divide_count % 2 == 1 else input_orientation

        short_divide_count = divide_count // 2
        long_divide_count = divide_count - short_divide_count

        if self.final_page_orientation == PageOrientation.PORTRAIT:
            width_divide_count = short_divide_count
            height_divide_count = long_divide_count
        else:
            width_divide_count = long_divide_count
            height_divide_count = short_divide_count

        self.final_page_size = final_sizes.get(self.final_page_orientation)
        self.columns = 2 ** width_divide_count
        self.rows = 2 ** height_divide_count
        self.input_page_size = PageSize(
            width_mm=self.final_page_size.width_mm / self.columns,
            height_mm=self.final_page_size.height_mm / self.rows,
        )

    def run_in_sandbox(self, command: List[str]) -> str:
        sandboxed_command = [SANDBOX_PATH, self.work_dir] + command
        print("Running command", " ".join(sandboxed_command))
        return subprocess.check_output(
            sandboxed_command,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
        )

    @staticmethod
    def _create_pages_to_print_iter(pages_to_print: Optional[str], input_page_count: int):
        if not pages_to_print:
            return range(input_page_count)

        def _create_iter_for_range(page_range: str):
            parts = page_range.split('-')
            # The range is 1-indexed inclusive, [start, end) is 0-indexed inclusive-exclusive.
            start = int(parts[0]) - 1
            # If len(parts) == 1 then parts[-1] = parts[0]
            end = min(int(parts[-1]), input_page_count)
            return range(start, end)

        return chain.from_iterable(map(_create_iter_for_range, pages_to_print.split(',')))

    def create_final_pages(self, input_pages_file: str, pages_to_print: str) -> str:
        out = os.path.join(self.work_dir, 'final_pages.pdf')
        reader = PdfReader(input_pages_file)
        writer = PdfWriter()

        used_input_pages = 0
        next_row = 0
        next_col = 0
        dest_page = None

        for page_index in self._create_pages_to_print_iter(pages_to_print, len(reader.pages)):
            page = reader.pages[page_index]
            page.transfer_rotation_to_content()
            if next_row == 0 and next_col == 0:
                dest_page = writer.add_blank_page(
                    width=self.final_page_size.width_pt(),
                    height=self.final_page_size.height_pt(),
                )

            dest_page.merge_transformed_page(
                page,
                Transformation().translate(
                    next_col * self.input_page_size.width_pt(),
                    # The y-coordinate starts from the bottom of the page
                    (self.rows - 1 - next_row) * self.input_page_size.height_pt(),
                ),
            )

            used_input_pages += 1
            next_col += 1
            if next_col == self.columns:
                next_row += 1
                next_col = 0
            if next_row == self.rows:
                next_row = 0

        if used_input_pages == 0:
            raise NoPagesToPrintException

        writer.compress_identical_objects()
        with open(out, "xb") as output_file:
            writer.write(output_file)
        return out
