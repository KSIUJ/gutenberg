from abc import ABC

from printing.processing.pages import PageSize, PageSizes


class BaseImpositionTemplate(ABC):
    def get_page_sizes(self, media_size: PageSize) -> PageSizes:
        pass

class StandardImpositionTemplate(BaseImpositionTemplate):
    def get_page_sizes(self, media_size: PageSize) -> PageSizes:
        if media_size.is_horizontal():
            raise ValueError("StandardImpositionTemplate expects a vertical media size")

        return PageSizes(
            portrait=media_size,
            landscape=media_size.rotated(),
        )

class BrochureImpositionTemplate(BaseImpositionTemplate):
    def get_page_sizes(self, media_size: PageSize) -> PageSizes:
        if media_size.is_horizontal():
            raise ValueError("BrochureImpositionTemplate expects a vertical media size")

        landscape_size = PageSize(width_mm=media_size.width_mm, height_mm=media_size.height_mm/2)
        return PageSizes(
            portrait=landscape_size.rotated(),
            landscape=landscape_size,
        )
