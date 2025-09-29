from dataclasses import dataclass
from enum import Enum

from printing.utils import MM_PER_PT


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

    def width_pt(self):
        return self.width_mm / MM_PER_PT

    def height_pt(self):
        return self.height_mm / MM_PER_PT


@dataclass(frozen=True)
class PageSizes:
    portrait: PageSize
    landscape: PageSize

    def get(self, orientation: PageOrientation) -> PageSize:
        if orientation == PageOrientation.PORTRAIT:
            return self.portrait
        return self.landscape
