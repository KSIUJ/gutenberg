"""
Testy dla printing.processing.converter

Bazując na konwencjach z pypdf:
- Używamy pytest markers (@pytest.mark.slow, @pytest.mark.samples)
- Docstring rozpoczyna się w sposób który można poprzedzić "This test ensures that..."
- Używamy fixtures dla powtarzalnych setupów
- Grupujemy testy w klasy dla lepszej organizacji
"""

import os
import tempfile
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pypdf import PdfReader

from printing.processing.converter import (
    ImageConverter, DocConverter, PdfConverter, PostScriptConverter,
    PwgRasterConverter, EarlyConverter, SandboxConverter,
    detect_file_format, get_converter, NoConverterAvailableError,
    CONVERTER_FOR_TYPE, CONVERTERS_LOCAL
)
from printing.processing.pages import PageSize, PageOrientation


@pytest.fixture
def work_dir():
    """A temporary working directory for converter tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_page_size():
    """Standard A4 page size fixture."""
    return PageSize(width_mm=210, height_mm=297)


@pytest.fixture
def mock_pdf_reader():
    """Mock PdfReader with configurable pages."""
    def _create_reader(page_configs):
        """
        Args:
            page_configs: List of tuples (width, height) for each page
        """
        mock_reader = Mock()
        pages = []
        for width, height in page_configs:
            page = Mock()
            page.mediabox.width = width
            page.mediabox.height = height
            pages.append(page)
        mock_reader.pages = pages
        return mock_reader
    return _create_reader


class TestFileFormatDetection:
    """Tests for file format detection functionality."""

    @patch('printing.processing.converter.magic.Magic')
    def test_pdf_format_is_detected_correctly(self, mock_magic_class):
        """PDF files are correctly identified by MIME type."""
        mock_mime = Mock()
        mock_mime.from_file.return_value = 'application/pdf'
        mock_magic_class.return_value = mock_mime
        
        result = detect_file_format('/path/to/file.pdf')
        
        assert result == 'application/pdf'

    @patch('printing.processing.converter.magic.Magic')
    def test_jpeg_format_is_detected_correctly(self, mock_magic_class):
        """JPEG images are correctly identified."""
        mock_mime = Mock()
        mock_mime.from_file.return_value = 'image/jpeg'
        mock_magic_class.return_value = mock_mime
        
        result = detect_file_format('/path/to/image.jpg')
        
        assert result == 'image/jpeg'

    @patch('printing.processing.converter.magic.Magic')
    def test_postscript_detection_from_verbose_output(self, mock_magic_class):
        """PostScript files are detected even when MIME type is text/plain."""
        mock_mime = Mock()
        mock_mime.from_file.return_value = 'text/plain'
        
        mock_verbose = Mock()
        mock_verbose.from_file.return_value = 'PostScript document text'
        
        mock_magic_class.side_effect = [mock_mime, mock_verbose]
        
        result = detect_file_format('/path/to/file.ps')
        
        assert result == 'application/postscript'

    @patch('printing.processing.converter.magic.Magic')
    def test_pwg_raster_detection_from_verbose_output(self, mock_magic_class):
        """PWG Raster files are detected from verbose magic output."""
        mock_mime = Mock()
        mock_mime.from_file.return_value = 'application/octet-stream'
        
        mock_verbose = Mock()
        mock_verbose.from_file.return_value = 'Cups Raster version 2'
        
        mock_magic_class.side_effect = [mock_mime, mock_verbose]
        
        result = detect_file_format('/path/to/file.pwg')
        
        assert result == 'image/pwg-raster'

class TestConverterRetrieval:
    """Tests for get_converter functionality."""

    def test_correct_converter_is_returned_for_pdf(self, work_dir):
        """PDF files get the PdfConverter."""
        converter = get_converter('application/pdf', work_dir)
        
        assert isinstance(converter, PdfConverter)
        assert converter.work_dir == work_dir

    def test_correct_converter_is_returned_for_image(self, work_dir):
        """Image files get the ImageConverter."""
        converter = get_converter('image/jpeg', work_dir)
        
        assert isinstance(converter, ImageConverter)
        assert converter.work_dir == work_dir

    def test_exception_raised_for_unsupported_format(self, work_dir):
        """Unsupported file formats raise NoConverterAvailableError."""
        with pytest.raises(NoConverterAvailableError) as exc_info:
            get_converter('application/x-unknown-format', work_dir)
        
        assert 'no converter available' in str(exc_info.value).lower()
        assert 'application/x-unknown-format' in str(exc_info.value)

    def test_converter_map_contains_all_local_converters(self):
        """All locally available converters are registered in the map."""
        for converter_class in CONVERTERS_LOCAL:
            for mime_type in converter_class.supported_types:
                assert mime_type in CONVERTER_FOR_TYPE

    def test_converter_map_uses_first_converter_for_duplicate_types(self):
        """When multiple converters support the same type, the first one is used."""
        from printing.processing.converter import _create_converter_map, Converter as BaseConverter
        
        # Mock scenario: two converters supporting the same type
        with patch('printing.processing.converter.CONVERTERS_LOCAL') as mock_local:
            class FakeConverter1(BaseConverter):
                supported_types = ['application/test']
                supported_extensions = ['.test']
                
                def preprocess(self, input_file: str):
                    pass
                def create_input_pdf(self, preprocess_result, input_page_size):
                    pass
                @classmethod
                def is_available(cls):
                    return True
            
            class FakeConverter2(BaseConverter):
                supported_types = ['application/test']  # Same type!
                supported_extensions = ['.test']
                
                def preprocess(self, input_file: str):
                    pass
                def create_input_pdf(self, preprocess_result, input_page_size):
                    pass
                @classmethod
                def is_available(cls):
                    return True
            
            mock_local.__iter__ = Mock(return_value=iter([FakeConverter1, FakeConverter2]))
            
            converter_map = _create_converter_map()
            
            # Should use the first converter (FakeConverter1)
            assert converter_map['application/test'] == FakeConverter1

    def test_converters_local_contains_only_available_converters(self):
        """CONVERTERS_LOCAL contains only converters that are available."""
        for converter_class in CONVERTERS_LOCAL:
            assert converter_class.is_available() is True

    def test_all_converters_in_local_are_in_all(self):
        """All converters in CONVERTERS_LOCAL are also in CONVERTERS_ALL."""
        from printing.processing.converter import CONVERTERS_ALL
        
        for converter_class in CONVERTERS_LOCAL:
            assert converter_class in CONVERTERS_ALL

class TestImageConverter:
    """Tests for ImageConverter functionality."""

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_landscape_orientation_detected_when_width_greater_than_height(
        self, mock_run, work_dir
    ):
        """Landscape orientation is detected for wide images."""
        mock_run.return_value = '1920 1080'  # width > height
        
        converter = ImageConverter(work_dir)
        result = converter.preprocess('/path/to/landscape.jpg')
        
        assert result.orientation == PageOrientation.LANDSCAPE
        assert result.preprocess_result_path == '/path/to/landscape.jpg'

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_portrait_orientation_detected_when_height_greater_than_width(
        self, mock_run, work_dir
    ):
        """Portrait orientation is detected for tall images."""
        mock_run.return_value = '1080 1920'  # width < height
        
        converter = ImageConverter(work_dir)
        result = converter.preprocess('/path/to/portrait.jpg')
        
        assert result.orientation == PageOrientation.PORTRAIT

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_pdf_creation_calls_imagemagick_convert(
        self, mock_run, work_dir, sample_page_size
    ):
        """PDF creation uses ImageMagick convert with correct parameters."""
        converter = ImageConverter(work_dir)
        preprocess_result = ImageConverter.PreprocessResult(
            orientation=PageOrientation.PORTRAIT,
            preprocess_result_path='/path/to/image.jpg'
        )
        
        result = converter.create_input_pdf(preprocess_result, sample_page_size)
        
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert 'convert' in call_args
        assert '-auto-orient' in call_args
        assert '-resize' in call_args
        assert result == os.path.join(work_dir, 'converted.pdf')

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_image_resized_with_5mm_margins(
        self, mock_run, work_dir, sample_page_size
    ):
        """Images are resized to fit page with 5mm margins on all sides."""
        converter = ImageConverter(work_dir)
        preprocess_result = ImageConverter.PreprocessResult(
            orientation=PageOrientation.PORTRAIT,
            preprocess_result_path='/path/to/image.jpg'
        )
        
        converter.create_input_pdf(preprocess_result, sample_page_size)
        
        call_args = mock_run.call_args[0][0]
        # Calculate expected dimensions: (210-10)mm * (300/25.4) ≈ 2362 pixels
        # (297-10)mm * (300/25.4) ≈ 3385 pixels
        resize_idx = call_args.index('-resize')
        resize_value = call_args[resize_idx + 1]
        assert 'x' in resize_value
        width, height = resize_value.split('x')
        assert int(width) > 2300 and int(width) < 2400
        assert int(height) > 3300 and int(height) < 3400

    @patch('shutil.which')
    def test_converter_available_when_imagemagick_installed(self, mock_which):
        """ImageConverter is available when convert binary exists."""
        mock_which.return_value = '/usr/bin/convert'
        
        assert ImageConverter.is_available() is True

    @patch('shutil.which')
    def test_converter_unavailable_when_imagemagick_missing(self, mock_which):
        """ImageConverter is unavailable when convert binary is missing."""
        mock_which.return_value = None
        
        assert ImageConverter.is_available() is False

class TestDocConverter:
    """Tests for DocConverter (LibreOffice) functionality."""

    @patch.object(DocConverter, 'run_in_sandbox')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('shutil.move')
    @patch('os.rmdir')
    @patch('os.makedirs')
    def test_docx_converted_to_pdf_using_libreoffice(
        self, mock_makedirs, mock_rmdir, mock_move, 
        mock_isfile, mock_listdir, mock_run, work_dir
    ):
        """DOCX files are converted to PDF using LibreOffice."""
        mock_listdir.return_value = ['document.pdf']
        mock_isfile.return_value = True
        
        converter = DocConverter(work_dir)
        result = converter.convert_to_pdf('/path/to/document.docx')
        
        # Verify LibreOffice was called
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert 'libreoffice' in call_args
        assert '--headless' in call_args
        assert '--convert-to' in call_args
        assert 'pdf' in call_args
        
        assert result == os.path.join(work_dir, 'converted.pdf')

    @patch.object(DocConverter, 'run_in_sandbox')
    @patch('os.listdir')
    @patch('os.makedirs')
    def test_exception_raised_when_libreoffice_produces_no_output(
        self, mock_makedirs, mock_listdir, mock_run, work_dir
    ):
        """Exception is raised when LibreOffice produces no output file."""
        mock_listdir.return_value = []  # No files in output directory
        
        converter = DocConverter(work_dir)
        
        with pytest.raises(Exception) as exc_info:
            converter.convert_to_pdf('/path/to/document.docx')
        
        assert 'Missing PDF after conversion' in str(exc_info.value)

    @patch.object(DocConverter, 'run_in_sandbox')
    @patch('os.listdir')
    @patch('os.makedirs')
    def test_exception_raised_when_libreoffice_produces_multiple_files(
        self, mock_makedirs, mock_listdir, mock_run, work_dir
    ):
        """Exception is raised when LibreOffice produces multiple files."""
        mock_listdir.return_value = ['file1.pdf', 'file2.pdf']
        
        converter = DocConverter(work_dir)
        
        with pytest.raises(Exception) as exc_info:
            converter.convert_to_pdf('/path/to/document.docx')
        
        assert 'multiple files' in str(exc_info.value).lower()

    @patch.object(DocConverter, 'run_in_sandbox')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_exception_raised_when_output_is_not_a_file(
        self, mock_makedirs, mock_isfile, mock_listdir, mock_run, work_dir
    ):
        """Exception is raised when LibreOffice output is not a file (e.g., directory)."""
        mock_listdir.return_value = ['output']
        mock_isfile.return_value = False  # Its a directory or doesnt exist
        
        converter = DocConverter(work_dir)
        
        with pytest.raises(Exception) as exc_info:
            converter.convert_to_pdf('/path/to/document.docx')
        
        assert 'not a file' in str(exc_info.value).lower()

    @patch.object(DocConverter, 'run_in_sandbox')
    @patch('os.listdir')
    @patch('os.path.isfile')
    @patch('os.makedirs')
    def test_exception_raised_when_output_is_not_pdf(
        self, mock_makedirs, mock_isfile, mock_listdir, mock_run, work_dir
    ):
        """Exception is raised when LibreOffice produces non-PDF output."""
        mock_listdir.return_value = ['document.txt']
        mock_isfile.return_value = True
        
        converter = DocConverter(work_dir)
        
        with pytest.raises(Exception) as exc_info:
            converter.convert_to_pdf('/path/to/document.docx')
        
        assert 'not a PDF' in str(exc_info.value)

    @patch('shutil.which')
    def test_converter_available_when_libreoffice_installed(self, mock_which):
        """DocConverter is available when LibreOffice is installed."""
        mock_which.return_value = '/usr/bin/libreoffice'
        
        assert DocConverter.is_available() is True

class TestPdfConverter:
    """Tests for PdfConverter functionality."""

    def test_pdf_file_returned_unchanged(self, work_dir):
        """PDF files are passed through without modification."""
        converter = PdfConverter(work_dir)
        input_path = '/path/to/existing.pdf'
        
        result = converter.convert_to_pdf(input_path)
        
        assert result == input_path

    def test_converter_always_available(self):
        """PdfConverter is always available (no external dependencies)."""
        assert PdfConverter.is_available() is True

class TestPostScriptConverter:
    """Tests for PostScriptConverter (Ghostscript) functionality."""

    @patch.object(PostScriptConverter, 'run_in_sandbox')
    def test_postscript_converted_using_ghostscript(self, mock_run, work_dir):
        """PostScript files are converted to PDF using Ghostscript."""
        converter = PostScriptConverter(work_dir)
        result = converter.convert_to_pdf('/path/to/file.ps')
        
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert 'gs' in call_args
        assert '-sDEVICE=pdfwrite' in call_args
        assert '-dSAFER' in call_args
        assert result == os.path.join(work_dir, 'converted.pdf')

    @patch('shutil.which')
    def test_converter_available_when_ghostscript_installed(self, mock_which):
        """PostScriptConverter is available when gs is installed."""
        mock_which.return_value = '/usr/bin/gs'
        
        assert PostScriptConverter.is_available() is True

class TestPwgRasterConverter:
    """Tests for PwgRasterConverter (CUPS) functionality."""

    @patch.object(PwgRasterConverter, 'run_in_sandbox')
    def test_pwg_raster_converted_using_cupsfilter(self, mock_run, work_dir):
        """PWG Raster files are converted using cupsfilter."""
        converter = PwgRasterConverter(work_dir)
        result = converter.convert_to_pdf('/path/to/file.pwg')
        
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert 'cupsfilter' in call_args
        assert '-i' in call_args
        assert 'image/pwg-raster' in call_args
        assert result == os.path.join(work_dir, 'converted.pdf')

    @patch('subprocess.check_output')
    @patch('shutil.which')
    def test_converter_checks_cupsfilter_filter_support(
        self, mock_which, mock_check_output
    ):
        """Converter availability checks if cupsfilter supports PWG format."""
        mock_which.return_value = '/usr/bin/cupsfilter'
        mock_check_output.return_value = b'Filter list'
        
        result = PwgRasterConverter.is_available()
        
        assert result is True
        assert mock_check_output.called

    @patch('shutil.which')
    def test_converter_unavailable_when_cupsfilter_missing(self, mock_which):
        """Converter is unavailable when cupsfilter is not installed."""
        mock_which.return_value = None
        
        assert PwgRasterConverter.is_available() is False

    @patch('subprocess.check_output')
    @patch('shutil.which')
    def test_converter_unavailable_when_cupsfilter_lacks_pwg_support(
        self, mock_which, mock_check_output
    ):
        """Converter is unavailable when cupsfilter doesn't support PWG format."""
        mock_which.return_value = '/usr/bin/cupsfilter'
        mock_check_output.side_effect = subprocess.CalledProcessError(
            returncode=1, 
            cmd=['cupsfilter', '--list-filters']
        )
        
        result = PwgRasterConverter.is_available()
        
        assert result is False
        assert mock_check_output.called

class TestEarlyConverter:
    """Tests for EarlyConverter base class functionality."""

    @patch('printing.processing.converter.PdfReader')
    def test_landscape_orientation_detected_from_pdf_pages(
        self, mock_pdf_reader_class, work_dir, mock_pdf_reader
    ):
        """Landscape orientation is detected when most pages are horizontal."""
        # 3 landscape pages, 1 portrait page
        mock_reader = mock_pdf_reader([
            (297, 210),  # landscape
            (297, 210),  # landscape
            (297, 210),  # landscape
            (210, 297),  # portrait
        ])
        mock_pdf_reader_class.return_value = mock_reader
        
        class TestConverter(EarlyConverter):
            def convert_to_pdf(self, input_file: str) -> str:
                return '/tmp/test.pdf'
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestConverter(work_dir)
        result = converter.preprocess('/path/to/file.pdf')
        
        assert result.orientation == PageOrientation.LANDSCAPE

    @patch('printing.processing.converter.PdfReader')
    def test_portrait_orientation_detected_from_pdf_pages(
        self, mock_pdf_reader_class, work_dir, mock_pdf_reader
    ):
        """Portrait orientation is detected when most pages are vertical."""
        # 1 landscape page, 3 portrait pages
        mock_reader = mock_pdf_reader([
            (297, 210),  # landscape
            (210, 297),  # portrait
            (210, 297),  # portrait
            (210, 297),  # portrait
        ])
        mock_pdf_reader_class.return_value = mock_reader
        
        class TestConverter(EarlyConverter):
            def convert_to_pdf(self, input_file: str) -> str:
                return '/tmp/test.pdf'
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestConverter(work_dir)
        result = converter.preprocess('/path/to/file.pdf')
        
        assert result.orientation == PageOrientation.PORTRAIT

    @patch('printing.processing.converter.PdfReader')
    def test_portrait_default_when_all_pages_square(
        self, mock_pdf_reader_class, work_dir, mock_pdf_reader
    ):
        """Portrait is the default orientation for square pages."""
        mock_reader = mock_pdf_reader([
            (210, 210),  # square
            (210, 210),  # square
        ])
        mock_pdf_reader_class.return_value = mock_reader
        
        class TestConverter(EarlyConverter):
            def convert_to_pdf(self, input_file: str) -> str:
                return '/tmp/test.pdf'
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestConverter(work_dir)
        result = converter.preprocess('/path/to/file.pdf')
        
        assert result.orientation == PageOrientation.PORTRAIT

    def test_create_input_pdf_returns_preprocessed_pdf(self, work_dir):
        """create_input_pdf returns the PDF created during preprocessing."""
        class TestConverter(EarlyConverter):
            def convert_to_pdf(self, input_file: str) -> str:
                return '/tmp/test.pdf'
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestConverter(work_dir)
        preprocess_result = EarlyConverter.PreprocessResult(
            orientation=PageOrientation.PORTRAIT,
            preprocess_result_path='/tmp/preprocessed.pdf'
        )
        page_size = PageSize(width_mm=210, height_mm=297)
        
        result = converter.create_input_pdf(preprocess_result, page_size)
        
        assert result == '/tmp/preprocessed.pdf'


class TestSandboxConverter:
    """Tests for SandboxConverter sandbox execution."""

    @patch('subprocess.check_output')
    @patch('printing.processing.converter.SANDBOX_PATH', '/path/to/sandbox.sh')
    def test_command_executed_in_sandbox_successfully(
        self, mock_check_output, work_dir
    ):
        """Commands are executed through sandbox wrapper."""
        mock_check_output.return_value = 'command output'
        
        class TestSandboxConverter(SandboxConverter):
            def preprocess(self, input_file: str):
                pass
            def create_input_pdf(self, preprocess_result, input_page_size):
                pass
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestSandboxConverter(work_dir)
        result = converter.run_in_sandbox(['echo', 'test'])
        
        assert result == 'command output'
        # Verify sandbox wrapper was used
        call_args = mock_check_output.call_args[0][0]
        assert call_args[0] == '/path/to/sandbox.sh'  # SANDBOX_PATH
        assert call_args[1] == work_dir
        assert 'echo' in call_args
        assert 'test' in call_args

    @patch('subprocess.check_output')
    def test_timeout_enforced_in_sandbox_execution(
        self, mock_check_output, work_dir
    ):
        """Sandbox execution enforces timeout limits."""
        mock_check_output.side_effect = subprocess.TimeoutExpired('cmd', 30)
        
        class TestSandboxConverter(SandboxConverter):
            def preprocess(self, input_file: str):
                pass
            def create_input_pdf(self, preprocess_result, input_page_size):
                pass
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestSandboxConverter(work_dir)
        
        with pytest.raises(subprocess.TimeoutExpired):
            converter.run_in_sandbox(['sleep', '1000'])

    @patch('shutil.which')
    def test_binary_exists_returns_true_when_binary_found(self, mock_which):
        """binary_exists returns True when binary is in PATH."""
        mock_which.return_value = '/usr/bin/convert'
        
        assert SandboxConverter.binary_exists('convert') is True

    @patch('shutil.which')
    def test_binary_exists_returns_false_when_binary_not_found(self, mock_which):
        """binary_exists returns False when binary is not in PATH."""
        mock_which.return_value = None
        
        assert SandboxConverter.binary_exists('nonexistent') is False


class TestIntegrationScenarios:
    """Integration tests covering full conversion workflows."""

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_complete_jpg_to_pdf_conversion_pipeline(
        self, mock_run, work_dir, sample_page_size
    ):
        """Complete JPG to PDF conversion workflow executes correctly."""
        # Mock identify for preprocess
        mock_run.side_effect = [
            '800 600',  # preprocess: identify returns dimensions
            None        # create_input_pdf: convert performs conversion
        ]
        
        converter = ImageConverter(work_dir)
        
        # Step 1: Preprocess
        preprocess_result = converter.preprocess('/path/to/image.jpg')
        assert preprocess_result.orientation == PageOrientation.LANDSCAPE
        
        # Step 2: Create PDF
        pdf_path = converter.create_input_pdf(preprocess_result, sample_page_size)
        
        assert pdf_path == os.path.join(work_dir, 'converted.pdf')
        assert mock_run.call_count == 2


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @patch('printing.processing.converter.magic.Magic')
    def test_empty_file_handled_gracefully(self, mock_magic_class):
        """Empty files are detected as octet-stream."""
        mock_mime = Mock()
        mock_mime.from_file.return_value = 'application/octet-stream'
        
        mock_verbose = Mock()
        mock_verbose.from_file.return_value = 'empty'
        
        mock_magic_class.side_effect = [mock_mime, mock_verbose]
        
        result = detect_file_format('/path/to/empty.file')
        
        assert result == 'application/octet-stream'

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_square_image_defaults_to_portrait(self, mock_run, work_dir):
        """Square images default to portrait orientation."""
        mock_run.return_value = '1000 1000'  # equal dimensions
        
        converter = ImageConverter(work_dir)
        result = converter.preprocess('/path/to/square.jpg')
        
        assert result.orientation == PageOrientation.PORTRAIT

    @patch('printing.processing.converter.PdfReader')
    def test_pdf_with_no_pages_defaults_to_portrait(
        self, mock_pdf_reader_class, work_dir
    ):
        """Empty PDFs default to portrait orientation."""
        mock_reader = Mock()
        mock_reader.pages = []
        mock_pdf_reader_class.return_value = mock_reader
        
        class TestConverter(EarlyConverter):
            def convert_to_pdf(self, input_file: str) -> str:
                return '/tmp/test.pdf'
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestConverter(work_dir)
        result = converter.preprocess('/path/to/empty.pdf')
        
        # Should default to PORTRAIT when no orientation can be determined
        assert result.orientation == PageOrientation.PORTRAIT


@pytest.mark.slow
class TestSecurityConstraints:
    """Tests for security-related functionality."""

    @patch('subprocess.check_output')
    def test_sandbox_timeout_is_enforced(self, mock_check_output, work_dir):
        """Sandbox enforces timeout to prevent infinite loops."""
        mock_check_output.side_effect = subprocess.TimeoutExpired(
            cmd='sleep 1000', 
            timeout=30
        )
        
        class TestSandboxConverter(SandboxConverter):
            def preprocess(self, input_file: str):
                pass
            def create_input_pdf(self, preprocess_result, input_page_size):
                pass
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestSandboxConverter(work_dir)
        
        with pytest.raises(subprocess.TimeoutExpired):
            converter.run_in_sandbox(['sleep', '1000'])

    @patch('subprocess.check_output')
    def test_sandbox_stderr_is_captured(self, mock_check_output, work_dir):
        """Sandbox captures stderr along with stdout."""
        class TestSandboxConverter(SandboxConverter):
            def preprocess(self, input_file: str):
                pass
            def create_input_pdf(self, preprocess_result, input_page_size):
                pass
            @classmethod
            def is_available(cls):
                return True
        
        converter = TestSandboxConverter(work_dir)
        converter.run_in_sandbox(['test_command'])
        
        # Verify stderr is set to STDOUT
        assert mock_check_output.call_args[1]['stderr'] == subprocess.STDOUT


@pytest.mark.slow
class TestPerformanceConstraints:
    """Tests for performance-related requirements."""

    @patch.object(ImageConverter, 'run_in_sandbox')
    def test_preprocess_completes_within_reasonable_time(
        self, mock_run, work_dir
    ):
        """Image preprocessing completes quickly."""
        import time
        
        mock_run.return_value = '800 600'
        
        converter = ImageConverter(work_dir)
        
        start_time = time.time()
        converter.preprocess('/path/to/image.jpg')
        elapsed = time.time() - start_time
            
        # With mocked subprocess, should be nearly instant
        assert elapsed < 1.0