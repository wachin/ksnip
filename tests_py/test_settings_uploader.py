from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, QSettings
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow
from ksnip_py.settings_dialog import SettingsDialog


class UploaderSelectorTest(unittest.TestCase):
    """Only the script uploader works, so the selector must show it."""

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("settings-uploader-test")
        QSettings().clear()
        self.window = MainWindow()
        self.dialog = SettingsDialog(
            self.window._current_settings_data(), self.window._watermark_store, self.window
        )

    def tearDown(self):
        self.dialog.close()
        self.dialog.deleteLater()
        self.window.close()
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def test_selector_is_disabled(self):
        self.assertFalse(self.dialog.uploader_type.isEnabled())

    def test_selector_shows_the_script_uploader(self):
        self.assertEqual(self.dialog.uploader_type.currentData(), "script")
        self.assertEqual(self.dialog.uploader_type.currentText(), self.dialog.tr("Script"))


if __name__ == "__main__":
    unittest.main()
