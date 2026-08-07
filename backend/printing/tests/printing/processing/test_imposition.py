import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock, call

from pypdf import PdfReader, PdfWriter, PageObject

from printing.processing.imposition import (
    ImpositionResult,
    BaseImpositionProcessor,
    SandboxImpositionProcessor,
    StandardImpositionProcessor,
    BookletImpositionProcessor,
    get_imposition_processor,
)
from printing.processing.pages import PageSize, PageSizes, PageOrientation

class TestImpositionResult:
    def test_imposition_result_creation(self):
        result = ImpositionResult(
            output_file="test.pdf",
            media_sheet_count=5,
            media_sheet_page_count=10
        )
        assert result.output_file == "test.pdf"
        assert result.media_sheet_count == 5
        assert result.media_sheet_page_count == 10

    def test_imposition_result_immutable(self):
        result = ImpositionResult(
            output_file="test.pdf",
            media_sheet_count=5,
            media_sheet_page_count=10
        )
        with pytest.raises(Exception):
            result.output_file = "new.pdf"


class TestBaseImpositionProcessor:
    def test_vertical_media_size_accepted(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False

        class ConcreteProcessor(BaseImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass

        processor = ConcreteProcessor(media_size)
        assert processor.media_size == media_size

    def test_horizontal_media_size_rejected(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = True

        class ConcreteProcessor(BaseImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass

        with pytest.raises(ValueError) as context:
            ConcreteProcessor(media_size)
        assert "vertical media size" in str(context.value)


class TestSandboxImpositionProcessor:
    def test_initialization(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp/test"

        class ConcreteProcessor(SandboxImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass

        processor = ConcreteProcessor(media_size, work_dir)
        assert processor.media_size == media_size
        assert processor.work_dir == work_dir

    @patch('printing.processing.imposition.subprocess.check_output')
    @patch('printing.processing.imposition.SANDBOX_PATH', '/sandbox')
    @patch('printing.processing.imposition.TASK_TIMEOUT_S', 30)
    def test_run_in_sandbox(self, mock_check_output):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp/test"

        class ConcreteProcessor(SandboxImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass

        processor = ConcreteProcessor(media_size, work_dir)
        mock_check_output.return_value = "output"

        result = processor.run_in_sandbox(["cmd", "arg1", "arg2"])

        mock_check_output.assert_called_once_with(
            ['/sandbox', work_dir, 'cmd', 'arg1', 'arg2'],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30
        )
        assert result == "output"


class TestStandardImpositionProcessor:
    def test_get_final_page_sizes(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        rotated_size = Mock(spec=PageSize)
        media_size.rotated.return_value = rotated_size

        processor = StandardImpositionProcessor(media_size, "/tmp")
        sizes = processor.get_final_page_sizes()

        assert sizes.portrait == media_size
        assert sizes.landscape == rotated_size

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_portrait_no_duplex(self, mock_open, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_page1 = Mock(spec=PageObject)
        mock_page1.rotate.return_value = mock_page1
        mock_page2 = Mock(spec=PageObject)
        mock_page2.rotate.return_value = mock_page2

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_dest_page = Mock()
        mock_writer.add_blank_page.return_value = mock_dest_page
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = StandardImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                False
            )

            assert result.media_sheet_count == 1
            assert result.media_sheet_page_count == 2
            assert result.output_file.endswith('output.pdf')

            mock_page1.rotate.assert_called_once_with(0)
            mock_page2.rotate.assert_called_once_with(0)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_landscape(self, mock_open, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_page = Mock(spec=PageObject)
        mock_page.rotate.return_value = mock_page

        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_dest_page = Mock()
        mock_writer.add_blank_page.return_value = mock_dest_page
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = StandardImpositionProcessor(media_size, tmpdir)
            processor.create_output_pdf(
                "input.pdf",
                PageOrientation.LANDSCAPE,
                False
            )

            mock_page.rotate.assert_called_once_with(90)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_duplex_odd_pages(self, mock_open, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_page = Mock(spec=PageObject)
        mock_page.rotate.return_value = mock_page

        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_dest_page = Mock()
        mock_writer.add_blank_page.return_value = mock_dest_page
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = StandardImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                True
            )

            # Should append a blank page to make the count even
            assert mock_writer.add_blank_page.call_count == 2
            assert result.media_sheet_count == 1

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_duplex_even_pages(self, mock_open, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_page1 = Mock(spec=PageObject)
        mock_page1.rotate.return_value = mock_page1
        mock_page2 = Mock(spec=PageObject)
        mock_page2.rotate.return_value = mock_page2

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_dest_page = Mock()
        mock_writer.add_blank_page.return_value = mock_dest_page
        mock_writer_class.return_value = mock_writer

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = StandardImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                True
            )

            assert mock_writer.add_blank_page.call_count == 2
            assert result.media_sheet_count == 1


class TestBookletImpositionProcessor:
    def test_get_final_page_sizes(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_mm = 210
        media_size.height_mm = 297

        half_size = Mock(spec=PageSize)
        rotated_half = Mock(spec=PageSize)

        with patch('printing.processing.imposition.PageSize') as mock_page_size_class:
            mock_page_size_class.return_value = half_size
            half_size.rotated.return_value = rotated_half

            processor = BookletImpositionProcessor(media_size, "/tmp")
            sizes = processor.get_final_page_sizes()

            mock_page_size_class.assert_called_once_with(width_mm=210, height_mm=148.5)
            assert sizes.portrait == rotated_half
            assert sizes.landscape == half_size

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_portrait_4_pages(self, mock_open, mock_transformation_class, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_pages = []
        for i in range(4):
            page = Mock(spec=PageObject)
            page.rotate.return_value = page
            mock_pages.append(page)

        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_blank_page = Mock()
        mock_writer.add_blank_page.return_value = mock_blank_page
        mock_writer_class.return_value = mock_writer

        mock_transformation = Mock()
        mock_transformation.translate.return_value = mock_transformation
        mock_transformation_class.return_value = mock_transformation

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BookletImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                False
            )

            assert result.media_sheet_count == 1
            assert result.media_sheet_page_count == 2
            assert mock_writer.add_blank_page.call_count == 2

            for page in mock_pages:
                page.rotate.assert_called_with(90)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_landscape(self, mock_open, mock_transformation_class, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_page = Mock(spec=PageObject)
        mock_page.rotate.return_value = mock_page

        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_blank_page = Mock()
        mock_writer.add_blank_page.return_value = mock_blank_page
        mock_writer_class.return_value = mock_writer

        mock_transformation = Mock()
        mock_transformation.translate.return_value = mock_transformation
        mock_transformation_class.return_value = mock_transformation

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BookletImpositionProcessor(media_size, tmpdir)
            processor.create_output_pdf(
                "input.pdf",
                PageOrientation.LANDSCAPE,
                False
            )

            mock_page.rotate.assert_called_with(0)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_8_pages(self, mock_open, mock_transformation_class, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_pages = []
        for i in range(8):
            page = Mock(spec=PageObject)
            page.rotate.return_value = page
            mock_pages.append(page)

        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_blank_page = Mock()
        mock_writer.add_blank_page.return_value = mock_blank_page
        mock_writer_class.return_value = mock_writer

        mock_transformation = Mock()
        mock_transformation.translate.return_value = mock_transformation
        mock_transformation_class.return_value = mock_transformation

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BookletImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                False
            )

            assert result.media_sheet_count == 2
            assert result.media_sheet_page_count == 4
            assert mock_writer.add_blank_page.call_count == 4

    # NEW TEST 3: Edge case for booklet missing pages to fill the sheets completely
    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_booklet_odd_pages(self, mock_open, mock_transformation_class, mock_writer_class, mock_reader_class):
        """Test how booklets handle odd page counts (e.g. 5 pages). Should create 2 sheets (8 pages)."""
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_pages = []
        for i in range(5):
            page = Mock(spec=PageObject)
            page.rotate.return_value = page
            mock_pages.append(page)

        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_blank_page = Mock()
        mock_writer.add_blank_page.return_value = mock_blank_page
        mock_writer_class.return_value = mock_writer

        mock_transformation = Mock()
        mock_transformation.translate.return_value = mock_transformation
        mock_transformation_class.return_value = mock_transformation

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BookletImpositionProcessor(media_size, tmpdir)
            result = processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                False
            )

            # 5 pages requires ceil(5/4) = 2 media sheets = 4 physical sides printed
            assert result.media_sheet_count == 2
            assert result.media_sheet_page_count == 4
            assert mock_writer.add_blank_page.call_count == 4

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    @patch('builtins.open', new_callable=Mock)
    def test_create_output_pdf_transformation_calls(self, mock_open, mock_transformation_class, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792

        mock_pages = []
        for i in range(4):
            page = Mock(spec=PageObject)
            page.rotate.return_value = page
            mock_pages.append(page)

        mock_reader = Mock()
        mock_reader.pages = mock_pages
        mock_reader_class.return_value = mock_reader

        mock_writer = Mock()
        mock_blank_page = Mock()
        mock_writer.add_blank_page.return_value = mock_blank_page
        mock_writer_class.return_value = mock_writer

        mock_transformation = Mock()
        mock_transformation.translate.return_value = mock_transformation
        mock_transformation_class.return_value = mock_transformation

        with tempfile.TemporaryDirectory() as tmpdir:
            processor = BookletImpositionProcessor(media_size, tmpdir)
            processor.create_output_pdf(
                "input.pdf",
                PageOrientation.PORTRAIT,
                False
            )

            translate_calls = [c for c in mock_transformation.translate.call_args_list]
            assert len(translate_calls) > 0


class TestGetImpositionProcessor:
    def test_get_standard_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"

        processor = get_imposition_processor("none", media_size, work_dir)

        assert isinstance(processor, StandardImpositionProcessor)
        assert processor.media_size == media_size
        assert processor.work_dir == work_dir

    def test_get_booklet_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"

        processor = get_imposition_processor("booklet", media_size, work_dir)

        assert isinstance(processor, BookletImpositionProcessor)
        assert processor.media_size == media_size
        assert processor.work_dir == work_dir

    def test_get_unknown_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"

        with pytest.raises(ValueError) as context:
            get_imposition_processor("unknown_template", media_size, work_dir)

        assert "Unknown imposition template" in str(context.value)

