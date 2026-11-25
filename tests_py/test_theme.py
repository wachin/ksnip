import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import QApplication

from ksnip_py.app import configure_qt_platform_theme
from ksnip_py.theme import THEME_DARK, THEME_LIGHT, THEME_SYSTEM, apply_theme, normalize_theme


APP = QApplication.instance() or QApplication([])


class PlatformThemeTest(unittest.TestCase):
    def test_qt6ct_is_selected_for_qt5ct_when_the_plugin_exists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_dir = Path(directory) / "platformthemes"
            plugin_dir.mkdir()
            (plugin_dir / "libqt6ct.so").touch()
            with (
                patch("ksnip_py.app.sys.platform", "linux"),
                patch("ksnip_py.app.QLibraryInfo.path", return_value=directory),
                patch.dict(os.environ, {"QT_QPA_PLATFORMTHEME": "qt5ct"}),
            ):
                configure_qt_platform_theme()
                self.assertEqual(os.environ["QT_QPA_PLATFORMTHEME"], "qt6ct")

    def test_an_explicit_gtk3_selection_is_respected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_dir = Path(directory) / "platformthemes"
            plugin_dir.mkdir()
            (plugin_dir / "libqt6ct.so").touch()
            with (
                patch("ksnip_py.app.sys.platform", "linux"),
                patch("ksnip_py.app.QLibraryInfo.path", return_value=directory),
                patch.dict(os.environ, {"QT_QPA_PLATFORMTHEME": "gtk3"}),
            ):
                configure_qt_platform_theme()
                self.assertEqual(os.environ["QT_QPA_PLATFORMTHEME"], "gtk3")

    def test_theme_names_are_normalized(self) -> None:
        self.assertEqual(normalize_theme("dark"), THEME_DARK)
        self.assertEqual(normalize_theme("LIGHT"), THEME_LIGHT)
        self.assertEqual(normalize_theme("unknown"), THEME_SYSTEM)
        self.assertEqual(normalize_theme(None), THEME_SYSTEM)

    def test_builtin_dark_and_light_palettes_are_contrasting(self) -> None:
        original_palette = APP.palette()
        original_style = APP.style().objectName()
        original_theme = QIcon.themeName()
        try:
            apply_theme(APP, THEME_DARK)
            dark_window = APP.palette().color(QPalette.ColorRole.Window)
            self.assertLess(dark_window.lightness(), 128)

            apply_theme(APP, THEME_LIGHT)
            light_window = APP.palette().color(QPalette.ColorRole.Window)
            self.assertGreater(light_window.lightness(), 128)
        finally:
            APP.setStyle(original_style)
            APP.setPalette(original_palette)
            QIcon.setThemeName(original_theme)

    def test_missing_qt6ct_plugin_leaves_the_environment_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with (
                patch("ksnip_py.app.sys.platform", "linux"),
                patch("ksnip_py.app.QLibraryInfo.path", return_value=directory),
                patch.dict(os.environ, {"QT_QPA_PLATFORMTHEME": "qt5ct"}),
            ):
                configure_qt_platform_theme()
                self.assertEqual(os.environ["QT_QPA_PLATFORMTHEME"], "qt5ct")


if __name__ == "__main__":
    unittest.main()
