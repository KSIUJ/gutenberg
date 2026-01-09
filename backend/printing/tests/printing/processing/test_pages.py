import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass

sys.modules['django'] = MagicMock()
sys.modules['django.contrib'] = MagicMock()
sys.modules['django.contrib.auth'] = MagicMock()
sys.modules['django.contrib.auth.models'] = MagicMock()
sys.modules['django.db'] = MagicMock()
sys.modules['django.db.models'] = MagicMock()
sys.modules['control'] = MagicMock()
sys.modules['control.models'] = MagicMock()

from pypdf import PdfReader, PdfWriter, PageObject

from printing.processing.pages import PageSize, PageSizes, PageOrientation

def test_page_size_is_vertical():
    ps = PageSize(width_mm=100, height_mm=200)
    assert ps.is_vertical() is True
    assert ps.is_horizontal() is False

def test_page_size_is_horizontal():
    ps = PageSize(width_mm=200, height_mm=100)
    assert ps.is_horizontal() is True
    assert ps.is_vertical() is False

def test_page_size_to_vertical():
    ps = PageSize(width_mm=200, height_mm=100)
    vertical_ps = ps.to_vertical()
    assert vertical_ps.width_mm == 100
    assert vertical_ps.height_mm == 200

def test_page_size_rotated():
    ps = PageSize(width_mm=100, height_mm=200)
    rotated_ps = ps.rotated()
    assert rotated_ps.width_mm == 200
    assert rotated_ps.height_mm == 100

def test_page_size_width_pt():
    ps = PageSize(width_mm=25.4, height_mm=50.8)
    assert abs(ps.width_pt() - 72) < 0.01  
    assert abs(ps.height_pt() - 144) < 0.01

def test_page_sizes_get():
    portrait = PageSize(width_mm=210, height_mm=297)
    landscape = PageSize(width_mm=297, height_mm=210)
    psizes = PageSizes(portrait=portrait, landscape=landscape)
    
    assert psizes.get(PageOrientation.PORTRAIT) == portrait
    assert psizes.get(PageOrientation.LANDSCAPE) == landscape

def test_page_orientation_rotate():
    assert PageOrientation.PORTRAIT.rotate() == PageOrientation.LANDSCAPE
    assert PageOrientation.LANDSCAPE.rotate() == PageOrientation.PORTRAIT

    