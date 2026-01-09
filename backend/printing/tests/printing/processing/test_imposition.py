import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass

# Mock Django PRZED wszystkimi innymi importami
sys.modules['django'] = MagicMock()
sys.modules['django.contrib'] = MagicMock()
sys.modules['django.contrib.auth'] = MagicMock()
sys.modules['django.contrib.auth.models'] = MagicMock()
sys.modules['django.db'] = MagicMock()
sys.modules['django.db.models'] = MagicMock()
sys.modules['control'] = MagicMock()
sys.modules['control.models'] = MagicMock()

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


class TestImpositionResult(unittest.TestCase):
    def test_imposition_result_creation(self):
        result = ImpositionResult(
            output_file="test.pdf",
            media_sheet_count=5,
            media_sheet_page_count=10
        )
        self.assertEqual(result.output_file, "test.pdf")
        self.assertEqual(result.media_sheet_count, 5)
        self.assertEqual(result.media_sheet_page_count, 10)

    def test_imposition_result_immutable(self):
        result = ImpositionResult(
            output_file="test.pdf",
            media_sheet_count=5,
            media_sheet_page_count=10
        )
        with self.assertRaises(Exception):
            result.output_file = "new.pdf"


class TestBaseImpositionProcessor(unittest.TestCase):
    def test_vertical_media_size_accepted(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        
        class ConcreteProcessor(BaseImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass
        
        processor = ConcreteProcessor(media_size)
        self.assertEqual(processor.media_size, media_size)

    def test_horizontal_media_size_rejected(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = True
        
        class ConcreteProcessor(BaseImpositionProcessor):
            def get_final_page_sizes(self):
                pass
            def create_output_pdf(self, final_pages_file, final_page_orientation, duplex_enabled):
                pass
        
        with self.assertRaises(ValueError) as context:
            ConcreteProcessor(media_size)
        self.assertIn("vertical media size", str(context.exception))


class TestSandboxImpositionProcessor(unittest.TestCase):
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
        self.assertEqual(processor.media_size, media_size)
        self.assertEqual(processor.work_dir, work_dir)

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
            stderr=unittest.mock.ANY,
            timeout=30
        )
        self.assertEqual(result, "output")


class TestStandardImpositionProcessor(unittest.TestCase):
    def test_get_final_page_sizes(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        rotated_size = Mock(spec=PageSize)
        media_size.rotated.return_value = rotated_size
        
        processor = StandardImpositionProcessor(media_size, "/tmp")
        sizes = processor.get_final_page_sizes()
        
        self.assertEqual(sizes.portrait, media_size)
        self.assertEqual(sizes.landscape, rotated_size)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    def test_create_output_pdf_portrait_no_duplex(self, mock_writer_class, mock_reader_class):
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
            
            self.assertEqual(result.media_sheet_count, 1)
            self.assertEqual(result.media_sheet_page_count, 2)
            self.assertTrue(result.output_file.endswith('output.pdf'))
            
            # Verify pages were rotated with 0 degrees (portrait)
            mock_page1.rotate.assert_called_once_with(0)
            mock_page2.rotate.assert_called_once_with(0)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    def test_create_output_pdf_landscape(self, mock_writer_class, mock_reader_class):
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
            
            # Verify page was rotated 90 degrees (landscape)
            mock_page.rotate.assert_called_once_with(90)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    def test_create_output_pdf_duplex_odd_pages(self, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792
        
        mock_page = Mock(spec=PageObject)
        mock_page.rotate.return_value = mock_page
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page]  # Odd number of pages
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
                True  # Duplex enabled
            )
            
            # Should add blank page for odd number
            self.assertEqual(mock_writer.add_blank_page.call_count, 2)
            self.assertEqual(result.media_sheet_count, 1)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    def test_create_output_pdf_duplex_even_pages(self, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792
        
        mock_page1 = Mock(spec=PageObject)
        mock_page1.rotate.return_value = mock_page1
        mock_page2 = Mock(spec=PageObject)
        mock_page2.rotate.return_value = mock_page2
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]  # Even number
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
                True  # Duplex enabled
            )
            
            # Should NOT add blank page for even number
            self.assertEqual(mock_writer.add_blank_page.call_count, 2)
            self.assertEqual(result.media_sheet_count, 1)


class TestBookletImpositionProcessor(unittest.TestCase):
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
            self.assertEqual(sizes.portrait, rotated_half)
            self.assertEqual(sizes.landscape, half_size)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    def test_create_output_pdf_portrait_4_pages(self, mock_transformation_class, mock_writer_class, mock_reader_class):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        media_size.width_pt.return_value = 612
        media_size.height_pt.return_value = 792
        
        # Create 4 mock pages
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
            
            # For 4 pages, we need 1 media sheet (2 pages: front and rear)
            self.assertEqual(result.media_sheet_count, 1)
            self.assertEqual(result.media_sheet_page_count, 2)
            self.assertEqual(mock_writer.add_blank_page.call_count, 2)
            
            # Pages should be rotated 90 degrees for portrait
            for page in mock_pages:
                page.rotate.assert_called_with(90)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    def test_create_output_pdf_landscape(self, mock_transformation_class, mock_writer_class, mock_reader_class):
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
            
            # Pages should be rotated 0 degrees for landscape
            mock_page.rotate.assert_called_with(0)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    def test_create_output_pdf_8_pages(self, mock_transformation_class, mock_writer_class, mock_reader_class):
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
            
            # For 8 pages, we need 2 media sheets (4 pages: 2 front and 2 rear)
            self.assertEqual(result.media_sheet_count, 2)
            self.assertEqual(result.media_sheet_page_count, 4)
            self.assertEqual(mock_writer.add_blank_page.call_count, 4)

    @patch('printing.processing.imposition.PdfReader')
    @patch('printing.processing.imposition.PdfWriter')
    @patch('printing.processing.imposition.Transformation')
    def test_create_output_pdf_transformation_calls(self, mock_transformation_class, mock_writer_class, mock_reader_class):
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
            
            # Check that translate was called for top pages
            translate_calls = [call for call in mock_transformation.translate.call_args_list]
            self.assertGreater(len(translate_calls), 0)


class TestGetImpositionProcessor(unittest.TestCase):
    def test_get_standard_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"
        
        processor = get_imposition_processor("none", media_size, work_dir)
        
        self.assertIsInstance(processor, StandardImpositionProcessor)
        self.assertEqual(processor.media_size, media_size)
        self.assertEqual(processor.work_dir, work_dir)

    def test_get_booklet_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"
        
        processor = get_imposition_processor("booklet", media_size, work_dir)
        
        self.assertIsInstance(processor, BookletImpositionProcessor)
        self.assertEqual(processor.media_size, media_size)
        self.assertEqual(processor.work_dir, work_dir)

    def test_get_unknown_processor(self):
        media_size = Mock(spec=PageSize)
        media_size.is_horizontal.return_value = False
        work_dir = "/tmp"
        
        with self.assertRaises(ValueError) as context:
            get_imposition_processor("unknown_template", media_size, work_dir)
        
        self.assertIn("Unknown imposition template", str(context.exception))

