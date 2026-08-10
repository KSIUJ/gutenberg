import os
import subprocess
import pytest
from unittest.mock import MagicMock, patch, mock_open

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
        fp = FinalPageProcessor(str(tmp_path), 4, mock_page_sizes, PageOrientation.PORTRAIT, True)
        assert fp.columns == 2
        assert fp.rows == 2

    def test_init_perfect_square_times_two(self, mock_page_sizes):
        fp = FinalPageProcessor(str(tmp_path), 2, mock_page_sizes, PageOrientation.PORTRAIT, True)
        assert fp.final_page_orientation == PageOrientation.LANDSCAPE

        def test_init_eight_pages_up(self, mock_page_sizes, tmp_path):
            fp = FinalPageProcessor(str(tmp_path), 8, mock_page_sizes, PageOrientation.PORTRAIT, True)
        assert fp.final_page_orientation == PageOrientation.LANDSCAPE
        assert fp.columns == 4
        assert fp.rows == 2

    def test_init_invalid_n(self, mock_page_sizes):
        with pytest.raises(ValueError):
            FinalPageProcessor(str(tmp_path), 3, mock_page_sizes, PageOrientation.PORTRAIT, True)

    @pytest.mark.parametrize("page_range, input_pages, expected", [
        ("1-2,4-5", 10, [0, 1, 3, 4]),
        (None, 3, [0, 1, 2]),
        ("", 2, [0, 1]),
        ("3-5", 4, [2, 3]),
        ("2,4,6", 5, [1, 3]),
        ("7-10", 5, []),
        ("5-3", 5, []),
        ("1,2,2,3", 3, [0, 1, 1, 2]),
        (" 1 , 3 - 4 ", 4, [0, 2, 3]),
        ("2-3,10", 10, [1, 2, 9]),
        # Extra edge cases requested in PR review
        ("1-2,3", 10, [0, 1, 2]),
        ("1,10", 10, [0, 9]),
        ("1-10", 10, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    ])
    def test_pages_to_print_iter_range(self, page_range, input_pages, expected):
        """Merged multiple tests into one to easily cover more edge cases."""
        it = FinalPageProcessor._create_pages_to_print_iter(page_range, input_pages)
        assert list(it) == expected

    @pytest.mark.parametrize("invalid_range", ["abc", "0,-1"])
    def test_pages_to_print_iter_rejects_malformed_tokens(self, invalid_range):
        # User input should be validated earlier, so malformed tokens still fail fast here
        with pytest.raises(ValueError):
            list(FinalPageProcessor._create_pages_to_print_iter(invalid_range, 5))

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

    fp = FinalPageProcessor(str(tmp_path), 1, mock_page_sizes, PageOrientation.PORTRAIT, fit_to_page=True)
    res = fp.create_final_pages("in.pdf", "1")
    assert "final_pages.pdf" in res

    # It ensures fit_to_page=False bypasses scaling entirely
    @patch("printing.processing.final_pages.PdfReader")
    @patch("printing.processing.final_pages.PdfWriter")
    @patch("builtins.open", new_callable=mock_open)
    def test_create_final_pages_fit_to_page_disabled(self, mock_file, mock_writer_cls, mock_reader_cls, mock_page_sizes):
        mock_reader = mock_reader_cls.return_value
        mock_writer = mock_writer_cls.return_value

        mock_page = MagicMock()
        for attr in ['trimbox', 'cropbox', 'bleedbox', 'artbox', 'mediabox']:
            setattr(mock_page, attr, RectangleObject((0, 0, 100, 100)))

        mock_reader.pages = [mock_page]
        mock_writer.add_blank_page.return_value = MagicMock()

        fp = FinalPageProcessor("/tmp", 1, mock_page_sizes, PageOrientation.PORTRAIT, fit_to_page=False)
        fp.create_final_pages("in.pdf", "1")

        mock_page.scale_by.assert_not_called()

    def test_create_final_pages_no_pages(self, mock_page_sizes):
        with patch("printing.processing.final_pages.PdfReader") as mock_reader_cls:
            mock_reader_cls.return_value.pages = []
            fp = FinalPageProcessor("/tmp", 1, mock_page_sizes, PageOrientation.PORTRAIT, False)
            with pytest.raises(NoPagesToPrintException):
                fp.create_final_pages("in.pdf", "")

    @patch("printing.processing.final_pages.subprocess.check_output")
    @patch("printing.processing.final_pages.SANDBOX_PATH", "/tmp/sandbox")
    @patch("printing.processing.final_pages.TASK_TIMEOUT_S", 30)
    def test_run_in_sandbox(self, mock_sub, mock_page_sizes, tmp_path):
        mock_sub.return_value = "ok"
        fp = FinalPageProcessor(str(tmp_path), 1, mock_page_sizes, PageOrientation.PORTRAIT, False)

        result = fp.run_in_sandbox(["ls"])

        assert result == "ok"
        mock_sub.assert_called_once_with(
            ["/tmp/sandbox", str(tmp_path), "ls"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=30
        )

