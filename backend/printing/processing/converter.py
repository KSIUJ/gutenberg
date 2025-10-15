import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import chain
from typing import List

import magic
from celery.worker.control import control_command
from pypdf import PdfReader

from printing.processing.pages import PageSize, PageOrientation
from printing.utils import SANDBOX_PATH, TASK_TIMEOUT_S, logger


class Converter(ABC):
    """
    A document to PDF converter class. The resulting PDF contains the pages used for further processing.
    The converter should keep the original page orientation.
    """

    @dataclass(frozen=True)
    class PreprocessResult:
        orientation: PageOrientation
        preprocess_result_path: str

    supported_types = []
    supported_extensions = []
    output_type = 'application/pdf'

    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    @abstractmethod
    def preprocess(self, input_file: str) -> PreprocessResult:
        """
        Determine the input data orientation and optionally perform initial conversion steps,
        which don't require knowing the Input Page size.
        """

        pass

    @abstractmethod
    def create_input_pdf(self, preprocess_result: PreprocessResult, input_page_size: PageSize) -> str:
        """
        Perform the conversion of the input file to PDF or return the PDF generated in `preprocess`.
        `input_page_size` can be used to generate the page size expected in the further steps,
        but returning pages in this size is not required in the converter classes.

        :return: The path to the resulting PDF which contains the Input Pages.
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


class EarlyConverter(SandboxConverter, ABC):
    """
    An abstract converter class which performs the conversion to PDF in the `preprocess` step
    by calling the user-provided `convert_to_pdf` method and determines the orientation based on
    the generated PDF.

    The resulting PDF will have the orientation and page size of the original document,
    `input_page_size` is ignored.
    """

    @abstractmethod
    def convert_to_pdf(self, input_file: str) -> str:
        """
        A method that converts `input_file` to PDF and returns the output file path.
        """

        pass

    def preprocess(self, input_file: str) -> "EarlyConverter.PreprocessResult":
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
        return EarlyConverter.PreprocessResult(
            orientation=dominant_orientation,
            preprocess_result_path=preprocess_result_path,
        )


    def create_input_pdf(self, preprocess_result: "EarlyConverter.PreprocessResult", input_page_size: PageSize) -> str:
        # The PDF was created in the `preprocess` step,
        # it might have dimensions different from `input_page_size`, but this will be handled
        # in the next processing steps.
        return preprocess_result.preprocess_result_path


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

    def create_input_pdf(self, preprocess_result: "ImageConverter.PreprocessResult", input_page_size: PageSize) -> str:
        out = os.path.join(self.work_dir, 'converted.pdf')

        pixels_per_inch = 300
        pixels_per_mm = pixels_per_inch / 25.4

        # Calculate the image size in pixels assuming a 5 mm margin on both sides
        fit_area_width = round((input_page_size.width_mm - 10) * pixels_per_mm)
        fit_area_height = round((input_page_size.height_mm - 10) * pixels_per_mm)

        page_width = round(input_page_size.width_mm * pixels_per_mm)
        page_height = round(input_page_size.height_mm * pixels_per_mm)

        # TODO: Use scaling options (like fit to page)
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


class DocConverter(EarlyConverter):
    supported_types = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/rtf', 'application/vnd.oasis.opendocument.text']
    supported_extensions = ['.doc', '.docx', '.rtf', '.odt']

    def convert_to_pdf(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'converted.pdf')

        # LibreOffice only allows specifying the output directory, not the output file name.
        # To make sure that the resulting file is identified correctly, we create an empty directory
        # and search for the resulting file there.
        out_dir = os.path.join(self.work_dir, 'converter_out')
        os.makedirs(out_dir)
        self.run_in_sandbox(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', out_dir, input_file])

        output_files = [os.path.join(out_dir, entry) for entry in os.listdir(out_dir)]
        if len(output_files) == 0:
            raise Exception("Missing PDF after conversion by LibreOffice")
        if len(output_files) > 1:
            raise Exception("LibreOffice generated multiple files during conversion")
        libreoffice_out = output_files[0]
        if not os.path.isfile(libreoffice_out):
            raise Exception("Output from LibreOffice conversion is not a file")
        if  os.path.splitext(libreoffice_out)[1] != '.pdf':
            raise Exception("Output from LibreOffice conversion is not a PDF")

        # The `move` is here mostly to ensure that the output file has a standard name
        # and thus will not contain spaces or other unexpected characters.
        shutil.move(libreoffice_out, out)
        os.rmdir(out_dir)
        return out

    @classmethod
    def is_available(cls):
        return cls.binary_exists('libreoffice')


class PwgRasterConverter(EarlyConverter):
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


class PostScriptConverter(EarlyConverter):
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
        return cls.binary_exists('gs')


class PdfConverter(EarlyConverter):
    supported_types = ['application/pdf']
    supported_extensions = ['.pdf']

    def convert_to_pdf(self, input_file: str) -> str:
        # no-op, the file is already PDF
        return input_file

    @classmethod
    def is_available(cls):
        return True


CONVERTERS_ALL = [ImageConverter, DocConverter, PwgRasterConverter, PdfConverter, PostScriptConverter]
"""
Converters supported by the current worker.
"""
CONVERTERS_LOCAL = [conv for conv in CONVERTERS_ALL if conv.is_available()]

def _create_converter_map() -> dict[str, type[Converter]]:
    result:  dict[str, type[Converter]] = dict()
    for conv_class in CONVERTERS_LOCAL:
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


def get_converter(input_type: str, work_dir: str) -> Converter:
    try:
        conv_class = CONVERTER_FOR_TYPE[input_type]
    except KeyError:
        raise NoConverterAvailableError(
            "Unable to convert {} - no converter available".format(input_type))
    return conv_class(work_dir)


@control_command(name="gutenberg_get_supported_formats")
def get_own_supported_formats(state) -> dict:
    """
    A Celery command to get the document formats supported by the current worker.
    `get_formats_supported_by_workers` uses this command.
    """

    return {
        "mime_types": list(chain.from_iterable(conv.supported_types for conv in CONVERTERS_LOCAL)),
        "extensions": list(chain.from_iterable(conv.supported_extensions for conv in CONVERTERS_LOCAL)),
    }


@dataclass
class SupportedFormats:
    mime_types: List[str]
    extensions: List[str]
    next_check: datetime


_cached_supported_formats: SupportedFormats = SupportedFormats([], [], datetime.now())
def get_formats_supported_by_workers(celery_app) -> SupportedFormats:
    """
    Query all Celery workers for their supported document MIME types and filename extensions.
    The response is temporarily cached in memory.
    """

    global _cached_supported_formats
    if datetime.now() >= _cached_supported_formats.next_check:
        logger.debug("Refreshing supported document formats")
        try:
            responses = celery_app.control.broadcast("gutenberg_get_supported_formats", reply=True, timeout=1)
            if len(responses) == 0:
                logger.warning("Got no response from workers when refreshing supported document formats")
                _cached_supported_formats.next_check = datetime.now() + timedelta(seconds=10)
            else:
                logger.info(f"Received {len(responses)} responses from workers: {str(responses)}")
                worker_responses = [worker_response for response in responses for worker_response in response.values()]

                # The `sorted` calls are used to keep the formats ordered in the order they appear in `CONVERTERS_LOCAL`.
                # This keeps related formats grouped together.
                #
                # All elements of the intersection must, by definition, also be present in the list in the first response,
                # so the `.index(x)` call should not fail.
                _cached_supported_formats = SupportedFormats(
                    mime_types=sorted(
                        set.intersection(*[set(response["mime_types"]) for response in worker_responses]),
                        key=lambda x: worker_responses[0]["mime_types"].index(x),
                    ),
                    extensions=sorted(
                        set.intersection(*[set(response["extensions"]) for response in worker_responses]),
                        key=lambda x: worker_responses[0]["extensions"].index(x),
                    ),
                    next_check = datetime.now() + timedelta(minutes=30)
                )
        except Exception as e:
            logger.error(f"Failed to refresh supported document formats: {e}", exec_info=True)
            _cached_supported_formats.next_check = datetime.now() + timedelta(seconds=30)

    return _cached_supported_formats
