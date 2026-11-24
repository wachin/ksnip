import os
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QSettings
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


class CaptureCursorTest(unittest.TestCase):
    def setUp(self) -> None:
        QSettings().clear()

    def tearDown(self) -> None:
        QSettings().clear()

    def test_cursor_is_baked_into_the_capture_and_not_added_as_an_item(self) -> None:
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

        self.assertEqual(canvas.image().pixelColor(5, 5), QColor("red"))
        self.assertEqual(canvas._items, [])

    def test_cursor_capture_is_off_by_default_and_toggleable(self) -> None:
        window = MainWindow()

        self.assertFalse(window.capture_cursor_action.isChecked())
        window.capture_cursor_action.setChecked(True)
        self.assertTrue(window._setting_bool("capture/include_cursor", False))


if __name__ == "__main__":
    unittest.main()
