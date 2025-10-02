import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from itertools import chain
from typing import List

import magic
from pypdf import PdfReader

from printing.processing.pages import PageSize, PageOrientation
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S, logger


class Converter(ABC):
    """
    A document to PDF converter class. The resulting PDF contains the Input Pages used for further processing.
    """

    @dataclass(frozen=True)
    class PreprocessResult:
        orientation: PageOrientation
        preprocess_result_path: str

    supported_types = []
    supported_extensions = []
    output_type = 'application/pdf'

    def __init__(self, work_dir: str, fit_to_page: bool):
        self.work_dir = work_dir
        self.fit_to_page = fit_to_page

    @abstractmethod
    def preprocess(self, input_file: str) -> PreprocessResult:
        """
        Determine the input data orientation and optionally perform initial conversion steps,
        which don't require knowing the Input Page size.
        """

        pass

    @abstractmethod
    def create_input_pages(self, preprocess_result: PreprocessResult, input_page_size: PageSize) -> str:
        """
        Place the preprocessed document data on the Input Pages.

        :return: The resulting PDF which contains the Input Pages.
        """

        pass

    @classmethod
    @abstractmethod
    def is_available(cls):
        pass


class SandboxConverter(Converter, ABC):
    def run_in_sandbox(self, command: List[str]) -> str:
        sandboxed_command = [SANDBOX_PATH, self.work_dir] + command
        return subprocess.check_output(
            sandboxed_command,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=TASK_TIMEOUT_S,
        )

    @staticmethod
    def binary_exists(name: str):
        return shutil.which(name) is not None


class ResizingConverter(SandboxConverter, ABC):
    """
    An abstract converter used for input formats which declare a page size (e.g., PDF, PostScript, PWG Raster, .docx)
    in the document data.
    """

    @abstractmethod
    def convert_to_pdf(self, input_file: str) -> str:
        """
        A method that converts `input_file` to PDF and returns the output file path.
        """

        pass

    def preprocess(self, input_file: str) -> "ResizingConverter.PreprocessResult":
        preprocess_result_path = self.convert_to_pdf(input_file)
        reader = PdfReader(preprocess_result_path)

        vertical_page_count = 0
        horizontal_page_count = 0

        for page in reader.pages:
            if page.mediabox.height > page.mediabox.width:
                vertical_page_count += 1
            if page.mediabox.width > page.mediabox.height:
                horizontal_page_count += 1

        if horizontal_page_count + vertical_page_count == 0:
            logger.warning("Failed to determine orientation in ResizingConverter")

        dominant_orientation = PageOrientation.LANDSCAPE if horizontal_page_count > vertical_page_count else PageOrientation.PORTRAIT
        return ResizingConverter.PreprocessResult(
            orientation=dominant_orientation,
            preprocess_result_path=preprocess_result_path,
        )


    def create_input_pages(self, preprocess_result: "ResizingConverter.PreprocessResult", input_page_size: PageSize) -> str:
        out = os.path.join(self.work_dir, 'input_pages.pdf')
        self.run_in_sandbox([
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dNOPAUSE', '-dBATCH', '-dSAFER',

            # Specify the page size of the resulting PDF to be the size of the Input Page
            '-dFIXEDMEDIA',
            f"-dDEVICEWIDTHPOINTS={input_page_size.width_pt()}",
            f"-dDEVICEHEIGHTPOINTS={input_page_size.height_pt()}",

            # FIXME: -dFitPage automatically rotates pages, this is not what we want.
            #       Preventing this is not easy in GhostScript, so the
            #       resizing to the Input Page size should happen in the FinalPageProcessor.
            *(['-dFitPage'] if self.fit_to_page else []),

            '-sOutputFile=' + out, preprocess_result.preprocess_result_path
        ])
        return out


class ImageConverter(SandboxConverter):
    supported_types = ['image/png', 'image/jpeg']
    supported_extensions = ['.png', '.jpg', '.jpeg']

    def preprocess(self, input_file: str) -> "ImageConverter.PreprocessResult":
        identify_result = self.run_in_sandbox(
            ['identify', '-auto-orient', '-format', '%w %h', input_file],
        )
        [width, height] = [int(size) for size in identify_result.split(' ')]
        orientation = PageOrientation.LANDSCAPE if width > height else PageOrientation.PORTRAIT
        return ImageConverter.PreprocessResult(orientation, input_file)

    def create_input_pages(self, preprocess_result: "ImageConverter.PreprocessResult", input_page_size: PageSize) -> str:
        out = os.path.join(self.work_dir, 'input_pages.pdf')

        pixels_per_inch = 300
        pixels_per_mm = pixels_per_inch / 25.4

        # Calculate the image size in pixels assuming a 5 mm margin on both sides
        fit_area_width = round((input_page_size.width_mm - 10) * pixels_per_mm)
        fit_area_height = round((input_page_size.height_mm - 10) * pixels_per_mm)

        page_width = round(input_page_size.width_mm * pixels_per_mm)
        page_height = round(input_page_size.height_mm * pixels_per_mm)

        # TODO: Use scaling options (like fit to page)
        # TODO: Add `-dAutoRotatePages=/None`?
        #       See https://unix.stackexchange.com/questions/442720/ghostscript-changes-orientation-of-pdf
        self.run_in_sandbox(
            [
                'convert', preprocess_result.preprocess_result_path,
                # Auto-orient the image based on the EXIF orientation tag
                '-auto-orient',
                # Resize the image to fit the "fit area"
                '-resize', f'{fit_area_width}x{fit_area_height}',
                # Place the resized image on the page
                '-gravity', 'center', '-background', 'white', '-extent', f"{page_width}x{page_height}",
                # Set the PDF density to print using the standard normal quality
                '-units', 'PixelsPerInch', '-density', f'{pixels_per_inch}x{pixels_per_inch}',
                "-page", f"{page_width}x{page_height}",
                out,
            ],
        )
        return out

    @classmethod
    def is_available(cls):
        return cls.binary_exists('convert')


class DocConverter(ResizingConverter):
    supported_types = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/rtf', 'application/vnd.oasis.opendocument.text']
    supported_extensions = ['.doc', '.docx', '.rtf', '.odt']

    def convert_to_pdf(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'converted.pdf')
        self.run_in_sandbox(['unoconv', '-o', out, input_file])
        return out

    @classmethod
    def is_available(cls):
        return cls.binary_exists('unoconv')


class PwgRasterConverter(ResizingConverter):
    supported_types = ['image/pwg-raster']
    supported_extensions = ['.pwg']

    def convert_to_pdf(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'converted.pdf')
        self.run_in_sandbox(['cupsfilter', '-i', 'image/pwg-raster', '-m', 'application/pdf', input_file, out])
        return out

    @classmethod
    def is_available(cls):
        if not cls.binary_exists("cupsfilter"):
            return False

        try:
            subprocess.check_output(
                ["cupsfilter", "--list-filters", "-i", "image/pwg-raster", '-m', 'application/pdf'],
                stderr=subprocess.STDOUT, timeout=5,
            )
            return True
        except subprocess.CalledProcessError:
            return False


class PostScriptConverter(ResizingConverter):
    supported_types = ['application/postscript']
    supported_extensions = ['.ps']

    def convert_to_pdf(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'converted.pdf')
        self.run_in_sandbox([
            'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
            '-dNOPAUSE', '-dBATCH', '-dSAFER',
            '-sOutputFile=' + out, input_file
        ])
        return out

    @classmethod
    def is_available(cls):
        return True


class PdfConverter(ResizingConverter):
    supported_types = ['application/pdf']
    supported_extensions = ['.pdf']

    def convert_to_pdf(self, input_file: str) -> str:
        # no-op, the file is already PDF
        return input_file

    @classmethod
    def is_available(cls):
        return True


CONVERTERS_ALL = [ImageConverter, DocConverter, PwgRasterConverter, PdfConverter, PostScriptConverter]
CONVERTERS = [conv for conv in CONVERTERS_ALL if conv.is_available()]
SUPPORTED_FILE_FORMATS = list(chain.from_iterable(conv.supported_types for conv in CONVERTERS))
SUPPORTED_EXTENSIONS = list(chain.from_iterable(conv.supported_extensions for conv in CONVERTERS))

def _create_converter_map() -> dict[str, type[Converter]]:
    result:  dict[str, type[Converter]] = dict()
    for conv_class in CONVERTERS:
        for input_type in conv_class.supported_types:
            if input_type in result:
                # If multiple converters for the same input type are available, use the first one
                pass
            result[input_type] = conv_class
    return result

CONVERTER_FOR_TYPE = _create_converter_map()


class NoConverterAvailableError(ValueError):
    pass


def detect_file_format(input_file: str):
    mime_detector = magic.Magic(mime=True)
    input_type = mime_detector.from_file(input_file)
    if input_type == 'text/plain' or input_type == 'application/octet-stream':
        verbose_detector = magic.Magic()
        verbose_type = verbose_detector.from_file(input_file)
        if 'PostScript' in verbose_type:
            input_type = 'application/postscript'
        elif 'Cups Raster version 2' in verbose_type:
            input_type = 'image/pwg-raster'
    return input_type


def get_converter(input_type: str, work_dir: str, fit_to_page: bool) -> Converter:
    try:
        conv_class = CONVERTER_FOR_TYPE[input_type]
    except KeyError:
        raise NoConverterAvailableError(
            "Unable to convert {} - no converter available".format(input_type))
    return conv_class(work_dir, fit_to_page)
