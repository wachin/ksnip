from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow
from ksnip_py.settings_dialog import SettingsDialog


class RememberSaveDirectoryTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("saver-defaults-test")
        QSettings().clear()
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def test_remember_directory_is_enabled_by_default(self):
        self.assertTrue(self.window._current_settings_data().saver_remember_directory)

    def test_settings_dialog_shows_it_checked_by_default(self):
        data = self.window._current_settings_data()
        dialog = SettingsDialog(data, self.window._watermark_store, self.window)
        self.assertTrue(dialog.saver_remember_directory.isChecked())

    def test_last_directory_is_reused_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            self.window._settings.setValue("paths/last_image_dir", directory)
            self.assertEqual(self.window._default_image_directory(), directory)

    def test_unchecking_it_ignores_the_last_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.window._settings.setValue("paths/last_image_dir", directory)
            self.window._settings.setValue("saver/remember_directory", False)
            self.assertNotEqual(self.window._default_image_directory(), directory)

    def test_open_directory_defaults_to_last_used_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            self.window._settings.setValue("paths/last_directory", directory)
            self.assertEqual(self.window._default_open_directory(), directory)

    def test_open_remember_directory_is_enabled_by_default(self):
        self.assertTrue(self.window._current_settings_data().open_remember_directory)
        self.assertTrue(
            str(self.window._settings.value("open/remember_last_directory")).lower()
            in {"true", "1"}
        )

    def test_settings_dialog_shows_open_remember_checked_by_default(self):
        data = self.window._current_settings_data()
        dialog = SettingsDialog(data, self.window._watermark_store, self.window)
        self.assertTrue(dialog.open_remember_directory.isChecked())

    def test_unchecking_open_remember_uses_the_capture_location(self):
        with tempfile.TemporaryDirectory() as directory:
            self.window._settings.setValue("paths/last_opened_image_dir", directory)
            self.window._settings.setValue("open/remember_last_directory", False)
            self.assertNotEqual(self.window._default_open_directory(), directory)

    def test_saving_updates_the_last_used_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            saved_path = str(Path(directory) / "saved.png")
            self.window._store_recent_image_path(saved_path)
            self.assertEqual(self.window._settings.value("paths/last_directory"), directory)
            self.assertEqual(self.window._settings.value("paths/last_image_dir"), directory)
            self.assertEqual(
                self.window._settings.value("paths/last_opened_image_dir"), directory
            )
            self.assertEqual(self.window._default_open_directory(), directory)

    def test_open_directory_falls_back_when_the_last_directory_is_gone(self):
        missing = "/nonexistent/ksnip-pyqt6-last-directory"
        self.window._settings.setValue("open/remember_last_directory", True)
        self.window._settings.setValue("paths/last_directory", missing)
        self.window._settings.setValue("paths/last_opened_image_dir", missing)
        self.window._settings.setValue("paths/last_image_dir", missing)
        self.assertNotEqual(self.window._default_open_directory(), missing)


if __name__ == "__main__":
    unittest.main()
