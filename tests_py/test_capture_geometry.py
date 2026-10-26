from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QByteArray
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow
from ksnip_py.settings_dialog import SettingsDialog


class CaptureGeometrySettingTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.window = MainWindow()

    def test_settings_dialog_has_checkbox(self):
        data = self.window._current_settings_data()
        dialog = SettingsDialog(data, self.window._watermark_store, self.window)
        self.assertTrue(hasattr(dialog, "remember_capture_geometry"))
        # Label must exist as a translatable source (locale-independent check).
        self.assertIn(
            self.window.tr("Remember capture window size and position"),
            dialog.remember_capture_geometry.text(),
        )

    def test_settings_round_trip(self):
        data = self.window._current_settings_data()
        data.application_remember_capture_geometry = True
        dialog = SettingsDialog(data, self.window._watermark_store, self.window)
        self.assertTrue(dialog.remember_capture_geometry.isChecked())
        back = dialog.settings_data()
        self.assertTrue(back.application_remember_capture_geometry)


class CaptureGeometryBehaviorTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.window = MainWindow()
        self.s = self.window._settings
        self.window.restoreGeometry = MagicMock()
        self.window.showMaximized = MagicMock()

    def test_restores_saved_geometry_when_enabled(self):
        self.s.setValue("application/remember_capture_geometry", True)
        geom = QByteArray(b"\x01\x00fakegeom")
        self.s.setValue("window/capture_geometry", geom)
        self.window._first_image_window_adjusted = False
        self.window._schedule_resize_to_content()
        self.window.restoreGeometry.assert_called_once_with(geom)
        self.assertTrue(self.window._first_image_window_adjusted)

    def test_no_restore_when_no_saved_geometry(self):
        self.s.setValue("application/remember_capture_geometry", True)
        self.s.remove("window/capture_geometry")
        self.window._first_image_window_adjusted = False
        self.window._schedule_resize_to_content()
        self.window.restoreGeometry.assert_not_called()

    def test_no_restore_when_setting_disabled(self):
        self.s.setValue("application/remember_capture_geometry", False)
        self.s.setValue("window/capture_geometry", QByteArray(b"x"))
        self.window._schedule_resize_to_content()
        self.window.restoreGeometry.assert_not_called()

    def test_persist_only_when_image_visible(self):
        self.s.setValue("application/remember_capture_geometry", True)
        self.s.remove("window/capture_geometry")
        self.window._editor_visible = True
        self.window.saveGeometry = MagicMock(return_value=QByteArray(b"geomdata"))
        self.window._persist_capture_geometry()
        self.assertEqual(self.s.value("window/capture_geometry"), QByteArray(b"geomdata"))

        self.s.remove("window/capture_geometry")
        self.window._editor_visible = False
        self.window._persist_capture_geometry()
        self.assertIsNone(self.s.value("window/capture_geometry"))


if __name__ == "__main__":
    unittest.main()
