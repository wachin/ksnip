import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, Qt, QEvent
from PyQt6.QtGui import QImage, QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, OverlayItem, Tool

APP = QApplication.instance() or QApplication([])


def blank_image(width: int = 300, height: int = 300) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    return image


def make_temp_sticker(path: str) -> None:
    image = QImage(20, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("red"))
    image.save(path)


def press_event(point: QPoint) -> QMouseEvent:
    return QMouseEvent(
        QEvent.Type.MouseButtonPress,
        point.toPointF(),
        point.toPointF(),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


class IllustratorGrabTest(unittest.TestCase):
    def _canvas_with_sticker(self):
        canvas = AnnotationCanvas()
        canvas.set_image(blank_image())
        directory = tempfile.mkdtemp()
        sticker = str(Path(directory) / "sticker.png")
        make_temp_sticker(sticker)
        canvas.set_sticker_path(sticker)
        canvas.set_illustrator_grab(True)
        canvas.set_switch_to_select_after_drawing(False)
        return canvas, sticker

    def test_grab_selected_sticker_on_second_click(self) -> None:
        canvas, _ = self._canvas_with_sticker()
        canvas.set_tool(Tool.STICKER)
        canvas._map_to_image = lambda p: QPoint(50, 50)
        canvas.mousePressEvent(press_event(QPoint(50, 50)))
        self.assertEqual(len(canvas._items), 1)
        self.assertTrue(canvas.has_single_selected_item())
        self.assertEqual(canvas._selected_item_indices, [0])

        canvas._map_to_image = lambda p: QPoint(50, 50)
        canvas.mousePressEvent(press_event(QPoint(50, 50)))
        self.assertEqual(len(canvas._items), 1, "grab must not create a new item")
        self.assertIsNotNone(canvas._drag_start, "grab must arm a drag")
        self.assertEqual(canvas._selected_item_indices, [0])

    def test_click_empty_space_creates_new_item(self) -> None:
        canvas, _ = self._canvas_with_sticker()
        canvas.set_tool(Tool.STICKER)
        canvas._map_to_image = lambda p: QPoint(50, 50)
        canvas.mousePressEvent(press_event(QPoint(50, 50)))
        self.assertEqual(len(canvas._items), 1)

        canvas._map_to_image = lambda p: QPoint(250, 250)
        canvas.mousePressEvent(press_event(QPoint(250, 250)))
        self.assertEqual(len(canvas._items), 2, "empty click must create a new item")

    def test_grab_applies_to_other_creation_tools(self) -> None:
        canvas, _ = self._canvas_with_sticker()
        rect = OverlayItem(
            Tool.RECT, QPoint(10, 10), QPoint(80, 80), QColor("blue"), 3
        )
        canvas._items.append(rect)
        canvas._select_single_item(0)
        canvas.set_tool(Tool.RECT)
        canvas.set_illustrator_grab(True)

        canvas._map_to_image = lambda p: QPoint(40, 40)
        canvas.mousePressEvent(press_event(QPoint(40, 40)))
        self.assertEqual(len(canvas._items), 1, "grab must not create a new item")
        self.assertIsNotNone(canvas._drag_start, "grab must arm a drag")
        self.assertEqual(canvas._selected_item_indices, [0])

    def test_disabling_grab_restores_old_behavior(self) -> None:
        canvas, _ = self._canvas_with_sticker()
        canvas.set_illustrator_grab(False)
        canvas.set_tool(Tool.STICKER)
        sticker = OverlayItem(
            Tool.STICKER, QPoint(10, 10), QPoint(60, 60), QColor("green"), 2,
            sticker_path=canvas.sticker_path(),
        )
        canvas._items.append(sticker)
        canvas._select_single_item(0)

        canvas._map_to_image = lambda p: QPoint(30, 30)
        canvas.mousePressEvent(press_event(QPoint(30, 30)))
        self.assertEqual(len(canvas._items), 2, "without grab, click must create a new item")


if __name__ == "__main__":
    unittest.main()
