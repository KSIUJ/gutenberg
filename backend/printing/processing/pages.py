from dataclasses import dataclass
from enum import Enum
from math import log2

class PageOrientation(Enum):
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"

    def rotate(self):
        if self == PageOrientation.PORTRAIT:
            return PageOrientation.LANDSCAPE
        return PageOrientation.PORTRAIT

@dataclass(frozen=True)
class PageSize:
    width_mm: float
    height_mm: float

    def is_vertical(self) -> bool:
        return self.width_mm < self.height_mm

    def is_horizontal(self) -> bool:
        return self.width_mm > self.height_mm

    def to_vertical(self) -> "PageSize":
        if self.is_horizontal():
            return PageSize(width_mm=self.height_mm, height_mm=self.width_mm)
        return self

    def rotated(self):
        return PageSize(width_mm=self.height_mm, height_mm=self.width_mm)


@dataclass(frozen=True)
class PageSizes:
    portrait: PageSize
    landscape: PageSize

    def get(self, orientation: PageOrientation) -> PageSize:
        if orientation == PageOrientation.PORTRAIT:
            return self.portrait
        return self.landscape


def divide_page_into_n_parts(n: int, final_sizes: PageSizes, input_orientation: PageOrientation) -> PageSize:
    """
    Finds the Input Page size based on the n-up and Input Page orientation settings and the Final Page sizes
    for the selected imposition template.

    Input Page orientation is not necessarily the orientation of the pages in the input file (e.g., PDF).
    The pages from the input file will be positioned on the Input Pages without rotating it.
    """

    divide_count = round(log2(n))
    if 2 ** divide_count != n:
        raise ValueError("n must be a power of 2")

    final_page_orientation = input_orientation.rotate() if divide_count % 2 == 1 else input_orientation

    short_divide_count = divide_count // 2
    long_divide_count = divide_count - short_divide_count

    if final_page_orientation == PageOrientation.PORTRAIT:
        width_divide_count = short_divide_count
        height_divide_count = long_divide_count
    else:
        width_divide_count = long_divide_count
        height_divide_count = short_divide_count

    final_page_size = final_sizes.get(final_page_orientation)

    return PageSize(
        width_mm=final_page_size.width_mm / (2 ** width_divide_count),
        height_mm=final_page_size.height_mm / (2 ** height_divide_count),
    )
