import sys
from unittest.mock import MagicMock, patch, mock_open

mock_obj = MagicMock()
for module in [
    "django", "django.conf", "django.db", "django.apps", 
    "django.contrib", "django.contrib.auth", "django.contrib.auth.models",
    "celery", "magic", "gutenberg.settings.local_settings"
]:
    sys.modules[module] = mock_obj

sys.modules["printing.utils"] = MagicMock()
sys.modules["control.models"] = MagicMock()
sys.modules["printing.utils"].SANDBOX_PATH = "/tmp/sandbox"
sys.modules["printing.utils"].TASK_TIMEOUT_S = 30

import pytest
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

from printing.processing.final_pages import (
    FinalPageProcessor, 
    NoPagesToPrintException, 
    PageOrientation, 
    PageSize, 
    PageSizes
)

@pytest.fixture
def mock_page_sizes():
    sizes = MagicMock(spec=PageSizes)
    portrait = PageSize(width_mm=210, height_mm=297)
    landscape = PageSize(width_mm=297, height_mm=210)
    sizes.get.side_effect = lambda orient: portrait if orient == PageOrientation.PORTRAIT else landscape
    return sizes

class TestFinalPageProcessor:

    def test_init_perfect_square(self, mock_page_sizes):
        fp = FinalPageProcessor("/tmp", 4, mock_page_sizes, PageOrientation.PORTRAIT, True)
        assert fp.columns == 2
        assert fp.rows == 2

    def test_init_perfect_square_times_two(self, mock_page_sizes):
        fp = FinalPageProcessor("/tmp", 2, mock_page_sizes, PageOrientation.PORTRAIT, True)
        assert fp.final_page_orientation == PageOrientation.LANDSCAPE

    def test_init_invalid_n(self, mock_page_sizes):
        with pytest.raises(ValueError):
            FinalPageProcessor("/tmp", 3, mock_page_sizes, PageOrientation.PORTRAIT, True)

    def test_pages_to_print_iter_none(self):
        it = FinalPageProcessor._create_pages_to_print_iter(None, 3)
        assert list(it) == [0, 1, 2]

    def test_pages_to_print_iter_range(self):
        it = FinalPageProcessor._create_pages_to_print_iter("1-2,4-5", 10)
        assert list(it) == [0, 1, 3, 4]

    @patch("printing.processing.final_pages.PdfReader")
    @patch("printing.processing.final_pages.PdfWriter")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_final_pages_success(self, mock_file, mock_writer_cls, mock_reader_cls, mock_page_sizes):
        mock_reader = mock_reader_cls.return_value
        mock_writer = mock_writer_cls.return_value
        
        mock_page = MagicMock()
        for attr in ['trimbox', 'cropbox', 'bleedbox', 'artbox', 'mediabox']:
            setattr(mock_page, attr, RectangleObject((0, 0, 100, 100)))
        
        mock_reader.pages = [mock_page]
        mock_dest_page = MagicMock()
        mock_writer.add_blank_page.return_value = mock_dest_page

        fp = FinalPageProcessor("/tmp", 1, mock_page_sizes, PageOrientation.PORTRAIT, fit_to_page=True)
        res = fp.create_final_pages("in.pdf", "1")
        assert "final_pages.pdf" in res

    def test_create_final_pages_no_pages(self, mock_page_sizes):
        with patch("printing.processing.final_pages.PdfReader") as mock_reader_cls:
            mock_reader_cls.return_value.pages = []
            fp = FinalPageProcessor("/tmp", 1, mock_page_sizes, PageOrientation.PORTRAIT, False)
            with pytest.raises(NoPagesToPrintException):
                fp.create_final_pages("in.pdf", "")

    def test_run_in_sandbox(self, mock_page_sizes):
        with patch("subprocess.check_output") as mock_sub:
            mock_sub.return_value = "ok"
            fp = FinalPageProcessor("/tmp", 1, mock_page_sizes, PageOrientation.PORTRAIT, False)
            assert fp.run_in_sandbox(["ls"]) == "ok"