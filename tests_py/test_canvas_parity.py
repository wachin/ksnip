import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, CutDialog


APP = QApplication.instance() or QApplication([])


def coordinate_image(width: int = 10, height: int = 8) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    for y in range(height):
        for x in range(width):
            image.setPixelColor(x, y, QColor((x * 20) % 256, (y * 20) % 256, 0))
    return image


class CropAndCutParityTest(unittest.TestCase):
    def test_crop_moves_overlays_and_undo_restores_them(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image())
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas.add_image_item(overlay, QPoint(6, 5))
        canvas._push_undo_state()

        self.assertTrue(canvas._crop_to_rect(QRect(3, 2, 6, 5)))
        self.assertEqual(canvas._items[0].start, QPoint(3, 3))
        canvas.undo()
        self.assertEqual(canvas._items[0].start, QPoint(6, 5))

    def test_cut_removes_a_full_axis_slice(self) -> None:
        source = coordinate_image()
        canvas = AnnotationCanvas()
        canvas.set_image(source)

        self.assertTrue(canvas.cut_slice(QRect(3, 2, 2, 2)))
        self.assertEqual(canvas._image.size(), QImage(8, 8, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(3, 4), source.pixelColor(5, 4))
        canvas.undo()
        self.assertEqual(canvas._image.size(), source.size())

    def test_cut_dialog_uses_explicit_orientation(self) -> None:
        dialog = CutDialog(coordinate_image(300, 180))
        self.assertEqual(dialog.cut_rect(), QRect(100, 0, 100, 180))
        dialog.horizontal.setChecked(True)
        self.assertEqual(dialog.cut_rect(), QRect(0, 40, 300, 100))


class ImageEffectParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = QImage(20, 12, QImage.Format.Format_ARGB32)
        self.image.fill(QColor("white"))
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(self.image)

    def test_effects_are_exclusive_and_non_destructive(self) -> None:
        self.assertTrue(self.canvas.set_image_effect("invert"))
        self.assertEqual(self.canvas.image().pixelColor(0, 0), QColor("black"))
        self.assertEqual(self.canvas.background_image().pixelColor(0, 0), QColor("white"))
        self.assertTrue(self.canvas.set_image_effect("none"))
        self.assertEqual(self.canvas.image().pixelColor(0, 0), QColor("white"))

    def test_drop_shadow_adds_margin_without_changing_background(self) -> None:
        self.canvas.set_image_effect("drop_shadow")
        rendered = self.canvas.image()
        self.assertEqual(rendered.size(), QImage(80, 74, QImage.Format.Format_ARGB32).size())
        self.assertEqual(self.canvas.background_image().size(), self.image.size())
        self.canvas._refresh()
        self.assertEqual(self.canvas._map_to_image(QPoint(30, 30)), QPoint(0, 0))
        self.assertIsNone(self.canvas._map_to_image(QPoint(10, 10)))


if __name__ == "__main__":
    unittest.main()
