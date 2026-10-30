from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, QPoint, QSettings, Qt
from PyQt6.QtGui import QColor, QImage, QMouseEvent
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, Tool
from ksnip_py.main_window import MainWindow

STICKER_POINT = QPoint(50, 50)


def blank_image(width: int = 300, height: int = 300) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    return image


def make_temp_sticker(directory: str) -> str:
    path = str(Path(directory) / "sticker.png")
    image = QImage(20, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("red"))
    image.save(path)
    return path


def mouse_event(kind: QEvent.Type, point: QPoint) -> QMouseEvent:
    return QMouseEvent(
        kind,
        point.toPointF(),
        point.toPointF(),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )


def press(point: QPoint = STICKER_POINT) -> QMouseEvent:
    return mouse_event(QEvent.Type.MouseButtonPress, point)


def double_click(point: QPoint = STICKER_POINT) -> QMouseEvent:
    return mouse_event(QEvent.Type.MouseButtonDblClick, point)


def double_click_on(canvas: AnnotationCanvas) -> None:
    """Replay the press and the double click Qt sends when a user double clicks.

    The second press of the sequence arrives as a double click event, so the
    first press is the only one that can place a sticker.
    """
    canvas.mousePressEvent(press())
    canvas.mouseDoubleClickEvent(double_click())


class StickerDoubleClickTest(unittest.TestCase):
    """Double-clicking a sticker hands it to the select tool."""

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("sticker-double-click-test")
        QSettings().clear()
        self.directory = tempfile.mkdtemp()

    def tearDown(self):
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def _canvas(self, illustrator_grab: bool = False) -> AnnotationCanvas:
        canvas = AnnotationCanvas()
        canvas.set_image(blank_image())
        canvas.set_sticker_path(make_temp_sticker(self.directory))
        canvas.set_illustrator_grab(illustrator_grab)
        canvas.set_switch_to_select_after_drawing(False)
        canvas.set_tool(Tool.STICKER)
        canvas._map_to_image = lambda point: STICKER_POINT
        return canvas

    def _place_sticker(self, canvas: AnnotationCanvas) -> None:
        canvas.mousePressEvent(press())
        self.assertEqual(len(canvas._items), 1)

    def test_double_click_on_sticker_requests_the_select_tool(self):
        canvas = self._canvas()
        self._place_sticker(canvas)
        requested = []
        canvas.select_tool_requested.connect(lambda: requested.append(True))
        double_click_on(canvas)
        self.assertEqual(requested, [True])
        self.assertTrue(canvas.has_single_selected_item())
        self.assertEqual(canvas._selected_item_indices, [0])

    def test_double_click_does_not_leave_the_copy_placed_by_the_press(self):
        canvas = self._canvas()
        self._place_sticker(canvas)
        double_click_on(canvas)
        self.assertEqual(len(canvas._items), 1)

    def test_double_click_on_empty_area_keeps_the_sticker_tool(self):
        canvas = self._canvas()
        requested = []
        canvas.select_tool_requested.connect(lambda: requested.append(True))
        canvas.mouseDoubleClickEvent(double_click())
        self.assertEqual(requested, [])

    def test_corner_handle_is_ready_after_the_double_click(self):
        canvas = self._canvas()
        self._place_sticker(canvas)
        double_click_on(canvas)
        # The main window activates the select tool when it receives the request.
        canvas.set_tool(Tool.SELECT)
        item = canvas._items[canvas._selected_item_indices[0]]
        corner = item.bounds().bottomRight()
        canvas._map_to_image = lambda point: corner
        canvas.mousePressEvent(press())
        self.assertIsNotNone(canvas._active_handle)

    def test_double_click_works_with_illustrator_grab_enabled(self):
        canvas = self._canvas(illustrator_grab=True)
        self._place_sticker(canvas)
        requested = []
        canvas.select_tool_requested.connect(lambda: requested.append(True))
        double_click_on(canvas)
        self.assertEqual(requested, [True])
        self.assertEqual(len(canvas._items), 1)
        self.assertEqual(canvas._selected_item_indices, [0])


class StickerDoubleClickWindowTest(unittest.TestCase):
    """The main window reacts to the request by activating the select tool."""

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("sticker-double-click-window-test")
        QSettings().clear()
        # Closing a window with edits would open the discard prompt.
        QSettings().setValue("saver/prompt_discard", False)
        self.directory = tempfile.mkdtemp()
        self.window = MainWindow()
        self.canvas = self.window.current_canvas()
        self.assertIsNotNone(self.canvas)
        self.canvas.set_image(blank_image())
        self.canvas.set_sticker_path(make_temp_sticker(self.directory))
        self.canvas.set_illustrator_grab(False)
        self.canvas.set_switch_to_select_after_drawing(False)
        self.canvas._map_to_image = lambda point: STICKER_POINT

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def test_double_click_switches_the_active_tool_to_select(self):
        self.window.set_tool(Tool.STICKER)
        self.canvas.mousePressEvent(press())
        self.assertEqual(len(self.canvas._items), 1)
        double_click_on(self.canvas)
        self.assertEqual(self.window._current_tool(), Tool.SELECT)
        self.assertTrue(self.window.select_action.isChecked())
        self.assertTrue(self.canvas.has_single_selected_item())
        self.assertEqual(len(self.canvas._items), 1)


if __name__ == "__main__":
    unittest.main()
