import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import Tool
from ksnip_py.color_picker import ColorPaletteMenu
from ksnip_py.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


class ColorPaletteMenuTest(unittest.TestCase):
    def test_default_palette_matches_kcolorpicker(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        self.assertEqual(len(palette._colors), 12)
        expected = [QColor(color) for color in (Qt.GlobalColor.red, Qt.GlobalColor.green, Qt.GlobalColor.blue, Qt.GlobalColor.yellow, Qt.GlobalColor.magenta, Qt.GlobalColor.cyan, Qt.GlobalColor.white, Qt.GlobalColor.black)]
        self.assertEqual(palette._colors[:8], expected)
        self.assertTrue(all(color.alpha() == 100 for color in palette._colors[8:]))

    def test_custom_color_is_added_and_selected(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        custom = QColor(12, 34, 56, 78)
        palette.select_color(custom)
        self.assertIn(custom, palette._colors)
        self.assertTrue(any(button.isChecked() for button in palette._buttons))

    def test_marker_mode_removes_alpha_choices(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        palette.select_color(QColor(12, 34, 56, 78))
        palette.set_show_alpha(False)
        self.assertEqual(len(palette._colors), 9)
        self.assertTrue(all(color.alpha() == 255 for color in palette._colors))


class MainWindowColorPickerTest(unittest.TestCase):
    def test_palette_applies_and_synchronizes_stroke_color(self) -> None:
        window = MainWindow()
        image = QImage(20, 20, QImage.Format.Format_ARGB32)
        image.fill(QColor("white"))
        canvas = window.current_canvas()
        canvas.set_image(image)
        selected = QColor(23, 45, 67, 120)
        window._apply_selected_color(selected)
        self.assertEqual(canvas.color(), selected)
        self.assertIn(selected, window.property_color_palette._colors)
        self.assertIn(selected, window.toolbox_color_palette._colors)

        window.set_tool(Tool.MARKER_PEN)
        self.assertTrue(all(color.alpha() == 255 for color in window.property_color_palette._colors))

    def test_zoom_picker_matches_the_original_controls_and_shortcuts(self) -> None:
        window = MainWindow()
        self.assertEqual(window.zoom_spinbox.minimum(), 10)
        self.assertEqual(window.zoom_spinbox.maximum(), 800)
        self.assertEqual(window.zoom_spinbox.singleStep(), 10)
        self.assertFalse(window.zoom_fit_button.isHidden())
        self.assertFalse(window.zoom_reset_button.isHidden())
        self.assertEqual(window.zoom_reset_action.shortcut().toString(), "Ctrl+0")
        self.assertEqual(window.zoom_fit_action.shortcut().toString(), "Ctrl+F")
        self.assertFalse(window.zoom_in_action.shortcut().isEmpty())
        self.assertFalse(window.zoom_out_action.shortcut().isEmpty())
        canvas = window.current_canvas()
        canvas.set_image(QImage(20, 20, QImage.Format.Format_ARGB32))
        window._update_actions()
        window.zoom_in_action.trigger()
        self.assertEqual(canvas.zoom_percent(), 110)
        self.assertEqual(window.zoom_spinbox.value(), 110)
        window.zoom_reset_action.trigger()
        self.assertEqual(canvas.zoom_percent(), 100)


if __name__ == "__main__":
    unittest.main()
