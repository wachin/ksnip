from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt6.QtCore import QByteArray, QSettings, QUrl
from PyQt6.QtGui import QGuiApplication, QShowEvent
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog

from ksnip_py.file_dialogs import (
    _GeometryFileDialog,
    _keep_dialog_on_screen,
    get_open_file_name,
    normalize_qt_file_dialog_url_settings,
)


APP = QApplication.instance() or QApplication([])


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

    def test_mojibake_shortcut_is_repaired_from_its_ascii_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pictures = root / "Imágenes"
            pictures.mkdir()
            corrupted = root / (
                "ImÃ\x83Â\x83Ã\x82Â\x83Ã\x83Â\x82ÃÂÂ\x83Ã\x83Â\x83"
                "Ã\x82Â\x82ÃÃ\x82ÂÃÂ\x82¡genes"
            )
            settings = QSettings(str(root / "QtProject.ini"), QSettings.Format.IniFormat)
            settings.beginGroup("FileDialog")
            settings.setValue(
                "shortcuts",
                [QUrl.fromLocalFile(str(corrupted)).toString(QUrl.ComponentFormattingOption.FullyEncoded)],
            )
            settings.endGroup()

            normalize_qt_file_dialog_url_settings(settings)
            settings.beginGroup("FileDialog")
            values = settings.value("shortcuts")
            settings.endGroup()

            self.assertEqual(QUrl(values[0]).toLocalFile(), str(pictures))

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

    def test_dialog_wrapper_normalizes_and_returns_the_selection(self) -> None:
        with (
            patch("ksnip_py.file_dialogs.normalize_qt_file_dialog_url_settings") as normalize,
            patch.object(QFileDialog, "exec", return_value=QDialog.DialogCode.Accepted),
            patch.object(QFileDialog, "selectedFiles", return_value=["/tmp/a.png"]),
            patch.object(QFileDialog, "selectedNameFilter", return_value="PNG"),
            patch.object(QFileDialog, "saveGeometry", return_value=QByteArray(b"geometry")),
            patch.object(QFileDialog, "restoreGeometry"),
        ):
            self.assertEqual(get_open_file_name(None, "Open"), ("/tmp/a.png", "PNG"))
        self.assertEqual(normalize.call_count, 2)

    def test_dialog_geometry_is_saved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / "app.ini"), QSettings.Format.IniFormat)
            with (
                patch("ksnip_py.file_dialogs._dialog_settings", return_value=settings),
                patch.object(QFileDialog, "exec", return_value=QDialog.DialogCode.Accepted),
                patch.object(QFileDialog, "selectedFiles", return_value=["/tmp/a.png"]),
                patch.object(QFileDialog, "selectedNameFilter", return_value="PNG"),
                patch.object(QFileDialog, "saveGeometry", return_value=QByteArray(b"geometry")),
            ):
                get_open_file_name(None, "Open")

        self.assertEqual(settings.value("dialogs/open_geometry"), QByteArray(b"geometry"))

    def test_offscreen_geometry_is_clamped_to_the_available_screen(self) -> None:
        dialog = QFileDialog()
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setGeometry(-500, -400, 300, 200)

        _keep_dialog_on_screen(dialog)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        frame = dialog.frameGeometry()
        self.assertGreaterEqual(frame.left(), screen.left())
        self.assertGreaterEqual(frame.top(), screen.top())
        self.assertLessEqual(frame.right(), screen.right())
        self.assertLessEqual(frame.bottom(), screen.bottom())

    def test_geometry_is_applied_when_the_dialog_is_shown(self) -> None:
        dialog = _GeometryFileDialog(
            None,
            "Open",
            "",
            "",
            geometry=QByteArray(b"geometry"),
        )
        with patch("ksnip_py.file_dialogs._restore_geometry") as restore:
            dialog.showEvent(QShowEvent())
        restore.assert_called_once()
        self.assertEqual(bytes(restore.call_args.args[1]), b"geometry")


if __name__ == "__main__":
    unittest.main()
