from __future__ import annotations

import os
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
