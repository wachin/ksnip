from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QColor, QFocusEvent, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, InlineTextEditor, Tool


class InlineTextEditorFocusTest(unittest.TestCase):
    """The editor must survive the activation focus change Windows sends."""

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.editor = InlineTextEditor()
        self.addCleanup(self.editor.deleteLater)
        self.accepted = []
        self.canceled = []
        self.editor.accepted.connect(lambda: self.accepted.append(True))
        self.editor.canceled.connect(lambda: self.canceled.append(True))

    def _focus_out(self, reason: Qt.FocusReason) -> None:
        self.editor.focusOutEvent(QFocusEvent(QEvent.Type.FocusOut, reason))

    def test_activation_focus_change_keeps_an_empty_editor_open(self):
        """Windows hands the focus back to the toolbar button after the click."""

        self._focus_out(Qt.FocusReason.ActiveWindowFocusReason)
        self.assertEqual(self.accepted, [], "the empty text item would be dropped")
        self.assertEqual(self.canceled, [])

    def test_activation_focus_change_accepts_typed_text(self):
        self.editor.setPlainText("Hola")
        self._focus_out(Qt.FocusReason.ActiveWindowFocusReason)
        self.assertEqual(self.accepted, [True])

    def test_clicking_another_widget_closes_an_empty_editor(self):
        self._focus_out(Qt.FocusReason.MouseFocusReason)
        self.assertEqual(self.accepted, [True])

    def test_popup_focus_does_not_close_the_editor(self):
        self._focus_out(Qt.FocusReason.PopupFocusReason)
        self.assertEqual(self.accepted, [])


class TextToolClickTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.canvas = AnnotationCanvas()
        image = QImage(320, 240, QImage.Format.Format_ARGB32)
        image.fill(QColor("#ffffff"))
        self.canvas.set_image(image)
        self.canvas.resize(320, 240)
        self.canvas.show()
        self.app.processEvents()
        self.addCleanup(self.canvas.deleteLater)
        self.addCleanup(self.canvas.close)

    def _drag(self, start, end) -> None:
        from PyQt6.QtCore import QPoint
        from PyQt6.QtTest import QTest

        QTest.mousePress(
            self.canvas,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(*start),
        )
        QTest.mouseMove(self.canvas, QPoint(*end))
        QTest.mouseRelease(
            self.canvas,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(*end),
        )
        self.app.processEvents()

    def test_dragging_with_the_text_tool_opens_the_editor(self):
        self.canvas.set_tool(Tool.TEXT)

        self._drag((40, 40), (180, 90))

        self.assertEqual(len(self.canvas._items), 1)
        self.assertEqual(self.canvas._items[0].kind, Tool.TEXT)
        self.assertIsNotNone(
            self.canvas._inline_text_editor,
            "the inline text editor did not stay open",
        )

    def test_clicking_with_the_text_tool_opens_the_editor(self):
        self.canvas.set_tool(Tool.TEXT)

        self._drag((60, 60), (60, 60))

        self.assertEqual(len(self.canvas._items), 1)
        self.assertIsNotNone(self.canvas._inline_text_editor)
        rect = self.canvas._items[0]
        self.assertGreaterEqual(rect.end.x() - rect.start.x(), 60)


if __name__ == "__main__":
    unittest.main()
