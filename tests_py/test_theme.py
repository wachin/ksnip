import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ksnip_py.app import configure_qt_platform_theme


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
