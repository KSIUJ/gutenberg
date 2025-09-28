from unittest import TestCase

from printing.processing.pages import PageSize


class PageSizeTest(TestCase):
    def vertical_init_should_work(self):
        page = PageSize(width_mm=210, height_mm=297)
        self.assertEqual(page.width_mm, 210)
        self.assertEqual(page.height_mm, 297)
        self.assertTrue(page.is_vertical())
        self.assertFalse(page.is_horizontal())

    def horizontal_init_should_work(self):
        page = PageSize(width_mm=297, height_mm=210)
        self.assertEqual(page.width_mm, 297)
        self.assertEqual(page.height_mm, 210)
        self.assertFalse(page.is_vertical())
        self.assertTrue(page.is_horizontal())

    def square_init_should_work(self):
        page = PageSize(width_mm=100, height_mm=100)
        self.assertEqual(page.width_mm, 100)
        self.assertEqual(page.height_mm, 100)
        self.assertFalse(page.is_vertical())
        self.assertFalse(page.is_horizontal())

    def to_vertical_should_not_modify_self(self):
        raise NotImplementedError

    def rotated_should_work(self):
        raise NotImplementedError
