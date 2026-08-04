import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, CutDialog, ModifyCanvasDialog, RotateDialog, ScaleDialog


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


class RotateAndFlipParityTest(unittest.TestCase):
    def test_rotate_dialog_exposes_original_operations(self) -> None:
        dialog = RotateDialog()
        self.assertEqual(dialog.operation(), ("rotate", 180))
        dialog.rotate_clockwise.setChecked(True)
        self.assertEqual(dialog.operation(), ("rotate", 90))
        dialog.rotate_counterclockwise.setChecked(True)
        self.assertEqual(dialog.operation(), ("rotate", -90))
        dialog.rotate_arbitrary.setChecked(True)
        dialog.arbitrary_angle.setValue(37)
        self.assertEqual(dialog.operation(), ("rotate", 37))
        dialog.flip_horizontal.setChecked(True)
        self.assertEqual(dialog.operation(), ("flip", "horizontal"))
        dialog.flip_vertical.setChecked(True)
        self.assertEqual(dialog.operation(), ("flip", "vertical"))

    def test_horizontal_flip_changes_background_only_and_supports_undo(self) -> None:
        source = coordinate_image(4, 3)
        overlay = QImage(1, 1, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(1, 1))

        self.assertTrue(canvas.flip_image("horizontal"))
        self.assertEqual(canvas._image.pixelColor(0, 1), source.pixelColor(3, 1))
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))

    def test_rotation_changes_background_only_and_supports_undo(self) -> None:
        source = coordinate_image(4, 3)
        overlay = QImage(1, 1, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(1, 1))

        self.assertTrue(canvas.rotate(90))
        self.assertEqual((canvas._image.width(), canvas._image.height()), (3, 4))
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))


class ScaleParityTest(unittest.TestCase):
    def test_dialog_synchronizes_pixel_and_percent_with_aspect_ratio(self) -> None:
        dialog = ScaleDialog(QImage(500, 250, QImage.Format.Format_ARGB32).size())
        dialog.width_pixel.setValue(250)
        self.assertEqual(dialog.width_percent.value(), 50)
        self.assertEqual(dialog.height_pixel.value(), 125)
        self.assertEqual(dialog.height_percent.value(), 50)

        dialog.height_percent.setValue(200)
        self.assertEqual(dialog.new_size(), QImage(1000, 500, QImage.Format.Format_ARGB32).size())

    def test_dialog_allows_non_uniform_scaling_when_aspect_is_disabled(self) -> None:
        dialog = ScaleDialog(QImage(500, 250, QImage.Format.Format_ARGB32).size())
        dialog.keep_aspect_ratio.setChecked(False)
        dialog.width_percent.setValue(50)
        dialog.height_percent.setValue(200)
        self.assertEqual(dialog.new_size(), QImage(250, 500, QImage.Format.Format_ARGB32).size())

    def test_scale_transforms_item_geometry_but_not_stroke_width(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(10, 8))
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas.add_image_item(overlay, QPoint(2, 2))
        original_width = canvas._items[0].pen_width

        self.assertTrue(canvas.scale_to_size(20, 4))
        self.assertEqual(canvas._items[0].start, QPoint(4, 1))
        self.assertEqual(canvas._items[0].end, QPoint(8, 2))
        self.assertEqual(canvas._items[0].pen_width, original_width)
        canvas.undo()
        self.assertEqual(canvas._image.size(), coordinate_image(10, 8).size())
        self.assertEqual(canvas._items[0].start, QPoint(2, 2))


class ModifyCanvasParityTest(unittest.TestCase):
    def test_restricted_dialog_keeps_the_background_inside_the_canvas(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.position_x.setValue(2)
        self.assertEqual(dialog.position_x.value(), 0)
        dialog.canvas_width.setValue(5)
        self.assertEqual(dialog.canvas_width.value(), 10)
        dialog.position_x.setValue(-3)
        self.assertEqual(dialog.canvas_width.value(), 13)

    def test_unrestricted_dialog_allows_cropping_from_any_origin(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.restricted.setChecked(False)
        dialog.position_x.setValue(2)
        dialog.position_y.setValue(1)
        dialog.canvas_width.setValue(5)
        dialog.canvas_height.setValue(4)
        self.assertEqual(dialog.canvas_rect(), QRect(2, 1, 5, 4))

    def test_preview_is_bounded_for_a_very_large_canvas(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.canvas_width.setValue(32768)
        dialog.canvas_height.setValue(32768)
        self.assertLessEqual(dialog.preview.pixmap().width(), 760)
        self.assertLessEqual(dialog.preview.pixmap().height(), 480)

    def test_modify_canvas_expands_moves_items_and_supports_undo(self) -> None:
        source = coordinate_image()
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(4, 3))

        self.assertTrue(canvas.modify_canvas_rect(QRect(-2, -1, 14, 10), QColor("magenta")))
        self.assertEqual(canvas._image.size(), QImage(14, 10, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(2, 1), source.pixelColor(0, 0))
        self.assertEqual(canvas._image.pixelColor(0, 0), QColor("magenta"))
        self.assertEqual(canvas._items[0].start, QPoint(6, 4))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(4, 3))

    def test_modify_canvas_can_crop_using_an_explicit_origin(self) -> None:
        source = coordinate_image()
        canvas = AnnotationCanvas()
        canvas.set_image(source)

        self.assertTrue(canvas.modify_canvas_rect(QRect(2, 1, 5, 4)))
        self.assertEqual(canvas._image.size(), QImage(5, 4, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(0, 0), source.pixelColor(2, 1))


class ZoomParityTest(unittest.TestCase):
    def test_zoom_uses_ten_percent_steps_and_original_limits(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image())
        canvas.set_zoom_percent(795)
        canvas.zoom_in()
        self.assertEqual(canvas.zoom_percent(), 800)
        canvas.set_zoom_percent(15)
        canvas.zoom_out()
        self.assertEqual(canvas.zoom_percent(), 10)
        canvas.reset_zoom()
        self.assertEqual(canvas.zoom_percent(), 100)

    def test_fit_zoom_keeps_aspect_ratio_and_stays_in_range(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(400, 200))
        canvas.fit_to_size(QImage(200, 200, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas.zoom_percent(), 50)
        canvas.fit_to_size(QImage(10000, 10000, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas.zoom_percent(), 800)


if __name__ == "__main__":
    unittest.main()
