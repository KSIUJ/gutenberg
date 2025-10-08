import os
import subprocess
from itertools import chain
from math import isqrt
from typing import List, Optional

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject

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
    fit_to_page: bool
    final_page_orientation: PageOrientation
    final_page_size: PageSize
    input_page_size: PageSize
    rows: int
    columns: int

    def __init__(self, work_dir: str, n: int, final_sizes: PageSizes, input_orientation: PageOrientation, fit_to_page: bool):
        self.work_dir = work_dir
        self.fit_to_page = fit_to_page

        short_parts = isqrt(n)
        if short_parts ** 2 == n:
            long_parts = short_parts
            self.final_page_orientation = input_orientation
        elif 2 * (short_parts ** 2) == n:
            long_parts = 2 * short_parts
            self.final_page_orientation = input_orientation.rotate()
        else:
            raise ValueError("n must be a perfect square or a perfect square times 2")

        if self.final_page_orientation == PageOrientation.PORTRAIT:
            self.columns = short_parts
            self.rows = long_parts
        else:
            self.columns = long_parts
            self.rows = short_parts

        self.final_page_size = final_sizes.get(self.final_page_orientation)
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

            if self.fit_to_page:
                scale = min(
                    self.input_page_size.width_pt() / page.trimbox.width,
                    self.input_page_size.height_pt() / page.trimbox.height,
                )
                page.scale_by(scale)

            left_x = next_col * self.input_page_size.width_pt()
            right_x = left_x + self.input_page_size.width_pt()
            target_center_x = (left_x + right_x) / 2
            # The y-coordinate starts from the bottom of the page
            bottom_y = (self.rows - 1 - next_row) * self.input_page_size.height_pt()
            top_y = bottom_y + self.input_page_size.height_pt()
            target_center_y = (bottom_y + top_y) / 2

            current_center_x = (page.trimbox.left + page.trimbox.right) / 2
            current_center_y = (page.trimbox.bottom + page.trimbox.top) / 2

            dx = target_center_x - current_center_x
            dy = target_center_y - current_center_y
            page.add_transformation(Transformation().translate(dx, dy))

            # Modifying `cropbox` might also appear to modify `trimbox`, `bleedbox` or `artbox`, because
            # if `trimbox`, `bleedbox` or `artbox` is not defined, then `cropbox` is used as the default value.
            # In the same manner `mediabox` is used as the default for all others if they are not defined.
            # Care must be taken to compute all the new values before modifying them.
            #
            # This behavior was the source of a bug in `pypdf` discovered while working on Gutenberg:
            # https://github.com/py-pdf/pypdf/issues/3487
            new_attrs = dict()
            for attr in ['trimbox', 'bleedbox', 'artbox', 'cropbox', 'mediabox']:
                current = getattr(page, attr)
                new_attrs[attr] = RectangleObject((current.left + dx, current.bottom + dy, current.right + dx, current.top + dy))
            for attr, value in new_attrs.items():
                setattr(page, attr, value)

            page.cropbox.bottom = max(page.cropbox.bottom, bottom_y)
            page.cropbox.top = max(page.cropbox.top, top_y)
            page.cropbox.left = max(page.cropbox.left, left_x)
            page.cropbox.right = min(page.cropbox.right, right_x)

            page.trimbox.bottom = max(page.trimbox.bottom, bottom_y)
            page.trimbox.top = min(page.trimbox.top, top_y)
            page.trimbox.left = max(page.trimbox.left, left_x)
            page.trimbox.right = min(page.trimbox.right, right_x)

            # TODO: When borderless printing is added, the bleed box for the outer pages can be expanded here
            page.bleedbox.bottom = max(page.bleedbox.bottom, bottom_y)
            page.bleedbox.top = min(page.bleedbox.top, top_y)
            page.bleedbox.left = max(page.bleedbox.left, left_x)
            page.bleedbox.right = min(page.bleedbox.right, right_x)

            dest_page.merge_page(page)

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
