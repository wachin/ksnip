from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QSettings, QUrl

from ksnip_py.file_dialogs import get_open_file_name, normalize_qt_file_dialog_url_settings


class FileDialogPersistenceTest(unittest.TestCase):
    def test_unicode_qurls_are_persisted_fully_encoded_and_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / "QtProject.ini"), QSettings.Format.IniFormat)
            settings.beginGroup("FileDialog")
            settings.setValue("shortcuts", [
                "file:///home/wachin/Imágenes",
                "file:///home/wachin/Música",
                "file:///home/wachin/Documentación",
            ])
            settings.setValue("history", ["file:///home/wachin/Imágenes/tutoriales"])
            settings.setValue("lastVisited", "file:///home/wachin/Música")
            settings.endGroup()

            normalize_qt_file_dialog_url_settings(settings)
            settings.sync()
            settings_file = settings.fileName()
            del settings

            settings = QSettings(settings_file, QSettings.Format.IniFormat)
            settings.beginGroup("FileDialog")
            shortcuts = settings.value("shortcuts")
            history = settings.value("history")
            last_visited = settings.value("lastVisited")
            settings.endGroup()

            self.assertEqual(shortcuts, [
                "file:///home/wachin/Im%C3%A1genes",
                "file:///home/wachin/M%C3%BAsica",
                "file:///home/wachin/Documentaci%C3%B3n",
            ])
            self.assertEqual(QUrl(shortcuts[0]).toLocalFile(), "/home/wachin/Imágenes")
            self.assertEqual(QUrl(shortcuts[1]).toLocalFile(), "/home/wachin/Música")
            self.assertEqual(history, ["file:///home/wachin/Im%C3%A1genes/tutoriales"])
            self.assertEqual(last_visited, "file:///home/wachin/M%C3%BAsica")

    def test_non_url_values_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / "QtProject.ini"), QSettings.Format.IniFormat)
            settings.beginGroup("FileDialog")
            settings.setValue("shortcuts", ["file:", "not a valid URL %"])
            settings.endGroup()
            normalize_qt_file_dialog_url_settings(settings)
            settings.beginGroup("FileDialog")
            values = settings.value("shortcuts")
            settings.endGroup()
            self.assertEqual(values[0], "file:")
            self.assertEqual(values[1], "not a valid URL %")

    def test_dialog_wrapper_normalizes_before_and_after_static_helper(self) -> None:
        with (
            patch("ksnip_py.file_dialogs.normalize_qt_file_dialog_url_settings") as normalize,
            patch("ksnip_py.file_dialogs.QFileDialog.getOpenFileName", return_value=("/tmp/a.png", "PNG")) as dialog,
        ):
            self.assertEqual(get_open_file_name(None, "Open"), ("/tmp/a.png", "PNG"))
        self.assertEqual(normalize.call_count, 2)
        dialog.assert_called_once_with(None, "Open")


if __name__ == "__main__":
    unittest.main()
