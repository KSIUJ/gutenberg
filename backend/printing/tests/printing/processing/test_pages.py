import pytest
from printing.processing.pages import PageSize, PageSizes, PageOrientation

# NEW TEST 1: Parametrized test covering all width/height ratios from the PR review
@pytest.mark.parametrize("width, height, is_vert, is_horiz", [
    (100, 300, True, False),   # width/height < 1/2
    (100, 200, True, False),   # width/height = 1/2
    (150, 200, True, False),   # width/height > 1/2, < 1
    (200, 200, False, False),  # width/height = 1 (Square)
    (200, 150, False, True),   # width/height > 1, < 2
    (200, 100, False, True),   # width/height = 2
    (300, 100, False, True),   # width/height > 2
])
def test_page_size_orientations_by_ratio(width, height, is_vert, is_horiz):
    """Test page size utility functions on different sizes and extreme ratios."""
    ps = PageSize(width_mm=width, height_mm=height)
    assert ps.is_vertical() is is_vert
    assert ps.is_horizontal() is is_horiz

def test_page_size_to_vertical():
    ps = PageSize(width_mm=200, height_mm=100)
    vertical_ps = ps.to_vertical()
    assert vertical_ps.width_mm == 100
    assert vertical_ps.height_mm == 200

    # Ensure it stays the same if already vertical
    ps2 = PageSize(width_mm=100, height_mm=200)
    assert ps2.to_vertical() == ps2

def test_page_size_rotated():
    ps = PageSize(width_mm=100, height_mm=200)
    rotated_ps = ps.rotated()
    assert rotated_ps.width_mm == 200
    assert rotated_ps.height_mm == 100

def test_page_size_pt_conversion():
    ps = PageSize(width_mm=25.4, height_mm=50.8)
    assert ps.width_pt() == pytest.approx(72, abs=0.01)
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

