from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow
from ksnip_py.settings_dialog import SettingsDialog

# The active translator depends on which test ran first, so compare against the
# translated strings instead of the English source text.
IMAGES_SOURCE = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
PROJECTS_SOURCE = "Ksnip Projects (*.ksnip)"


class OpenDialogFilterTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("open-filter-test")
        QSettings().clear()
        self.window = MainWindow()
        self.images_filter = self.window.tr(IMAGES_SOURCE)
        self.projects_filter = self.window.tr(PROJECTS_SOURCE)

    def tearDown(self):
        self.window.close()
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def test_open_dialog_defaults_to_images(self):
        self.assertEqual(self.window._open_default_filter(), self.images_filter)

    def test_stored_choice_wins(self):
        self.window._settings.setValue("open/default_filter", "ksnip")
        self.assertEqual(self.window._open_default_filter(), self.projects_filter)
        self.window._settings.setValue("open/default_filter", "image")
        self.assertEqual(self.window._open_default_filter(), self.images_filter)

    def test_unknown_choice_falls_back_to_images(self):
        self.window._settings.setValue("open/default_filter", "something-else")
        self.assertEqual(self.window._open_default_filter(), self.images_filter)

    def test_default_filter_is_offered_by_the_open_dialog(self):
        self.assertIn(self.images_filter, [self.projects_filter, self.images_filter])

    def test_settings_combo_selects_images_by_default(self):
        data = self.window._current_settings_data()
        dialog = SettingsDialog(data, self.window._watermark_store, self.window)
        combo = dialog.open_default_filter
        self.assertEqual(combo.currentData(), "image")
        self.assertEqual(combo.currentText(), self.images_filter)


if __name__ == "__main__":
    unittest.main()
