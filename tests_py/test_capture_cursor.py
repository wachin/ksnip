import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QSettings
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import Tool
from ksnip_py.capture import CaptureResult, CursorCaptureIndicator
from ksnip_py.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


class CaptureCursorTest(unittest.TestCase):
    def setUp(self) -> None:
        QSettings().clear()

    def tearDown(self) -> None:
        QSettings().clear()

    def test_cursor_is_added_as_a_movable_fixed_size_item(self) -> None:
        window = MainWindow()
        base = QImage(20, 20, QImage.Format.Format_ARGB32)
        base.fill(QColor("white"))
        cursor = QImage(4, 4, QImage.Format.Format_ARGB32)
        cursor.fill(QColor("red"))
        result = SimpleNamespace(
            pixmap=QPixmap.fromImage(base),
            cursor_image=cursor,
            cursor_position=QPoint(5, 5),
        )

        window._load_capture_result(result, "Test capture")
        canvas = window.current_canvas()

        self.assertEqual(len(canvas._items), 1)
        item = canvas._items[0]
        self.assertEqual(item.kind, Tool.IMAGE)
        self.assertTrue(item.fixed_size)
        self.assertEqual(item.start, QPoint(5, 5))
        self.assertEqual(canvas._handle_points(item), {})
        self.assertIsNone(canvas._find_handle_at(item, QPoint(7, 7)))
        self.assertEqual(canvas.background_image().pixelColor(5, 5), QColor("white"))
        self.assertEqual(canvas.image().pixelColor(5, 5), QColor("red"))

    def test_cursor_is_only_added_when_a_capture_delay_is_set(self) -> None:
        window = MainWindow()
        base = QImage(20, 20, QImage.Format.Format_ARGB32)
        base.fill(QColor("white"))
        cursor = QImage(4, 4, QImage.Format.Format_ARGB32)
        cursor.fill(QColor("red"))
        without_cursor = CaptureResult(QPixmap.fromImage(base), "rect-area", QPoint())
        with_cursor = CaptureResult(QPixmap.fromImage(base), "rect-area", QPoint())

        window._settings.setValue("capture/cursor_arrow", False)
        with patch("ksnip_py.main_window.grab_x11_cursor", return_value=(cursor, QPoint(2, 2))):
            with patch.object(window, "_wait_for_capture_delay"):
                window._capture_cursor_override = True
                window._capture_delay_override_seconds = 0
                without_delay = window._capture_with_preferences(lambda: without_cursor)

                window._capture_cursor_override = True
                window._capture_delay_override_seconds = 1
                with_delay = window._capture_with_preferences(lambda: with_cursor)

        self.assertIsNone(without_delay.cursor_image)
        self.assertEqual(with_delay.cursor_image, cursor)

    def test_arrow_pointer_is_the_default_cursor_shape(self) -> None:
        window = MainWindow()
        self.assertTrue(window.capture_cursor_arrow_action.isChecked())
        self.assertFalse(window._arrow_cursor_image().isNull())

    def test_cursor_blink_indicator_keeps_the_pointer_area_transparent(self) -> None:
        indicator = CursorCaptureIndicator()
        image = indicator.grab().toImage()

        self.assertEqual(image.pixelColor(42, 42).alpha(), 0)
        self.assertGreater(image.pixelColor(42, 8).alpha(), 0)
        indicator.deleteLater()

    def test_delayed_capture_uses_the_standard_arrow_by_default(self) -> None:
        window = MainWindow()
        base = QImage(20, 20, QImage.Format.Format_ARGB32)
        base.fill(QColor("white"))
        capture = CaptureResult(QPixmap.fromImage(base), "rect-area", QPoint())
        ibeam = QImage(4, 4, QImage.Format.Format_ARGB32)
        ibeam.fill(QColor("red"))

        with patch("ksnip_py.main_window.grab_x11_cursor", return_value=(ibeam, QPoint(0, 0))):
            with patch.object(window, "_wait_for_capture_delay"):
                window._capture_cursor_override = True
                window._capture_delay_override_seconds = 1
                result = window._capture_with_preferences(lambda: capture)

        self.assertIsNotNone(result.cursor_image)
        self.assertEqual(result.cursor_image.width(), 28)
        self.assertEqual(result.cursor_image.height(), 28)

    def test_cursor_capture_is_off_by_default_and_toggleable(self) -> None:
        window = MainWindow()

        self.assertFalse(window.capture_cursor_action.isChecked())
        window.capture_cursor_action.setChecked(True)
        self.assertTrue(window._setting_bool("capture/include_cursor", False))


if __name__ == "__main__":
    unittest.main()
