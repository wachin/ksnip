from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QByteArray, QSettings
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow
from ksnip_py.settings_dialog import SettingsDialog


class CaptureGeometrySettingTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self.window = MainWindow()
        self.addCleanup(self.window.close)

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
        # A real QSettings needs an organization name; without it Qt reports
        # AccessError and silently drops every write. Use a temporary INI file so
        # the tests never touch the user's configuration.
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.s = QSettings(
            str(Path(self._tmp.name) / "settings.ini"), QSettings.Format.IniFormat
        )
        self.window = MainWindow()
        self.window._settings = self.s
        self.addCleanup(self.window.close)
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

    def test_hiding_to_tray_persists_the_capture_geometry(self):
        """Closing or minimizing to the tray never reaches closeEvent()."""

        self.s.setValue("application/remember_capture_geometry", True)
        self.s.remove("window/capture_geometry")
        self.window._editor_visible = True
        self.window.saveGeometry = MagicMock(return_value=QByteArray(b"traygeom"))

        self.window.hide_to_tray()

        self.assertEqual(self.s.value("window/capture_geometry"), QByteArray(b"traygeom"))


class TrayRestoreStateTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.s = QSettings(
            str(Path(self._tmp.name) / "settings.ini"), QSettings.Format.IniFormat
        )
        self.window = MainWindow()
        self.window._settings = self.s
        self.addCleanup(self.window.close)
        self.window.show()
        self.app.processEvents()

    def test_restoring_from_tray_keeps_a_maximized_window(self):
        from PyQt6.QtCore import Qt

        self.window.showMaximized()
        self.app.processEvents()
        self.assertTrue(self.window.isMaximized())

        self.window.hide_to_tray()
        self.assertEqual(
            self.window._tray_restore_state, Qt.WindowState.WindowMaximized
        )

        self.window.show_from_tray()
        self.app.processEvents()
        self.assertTrue(
            self.window.isMaximized(),
            "a maximized window came back at its normal size after the tray",
        )

    def test_restoring_from_tray_keeps_a_normal_window(self):
        self.window.showNormal()
        self.app.processEvents()

        self.window.hide_to_tray()
        self.window.show_from_tray()
        self.app.processEvents()

        self.assertFalse(self.window.isMaximized())

    def test_minimizing_sends_the_window_to_the_tray(self):
        """Hiding during the native minimize leaves the window mapped again."""

        import time

        from PyQt6.QtCore import Qt

        self.window._tray_icon = MagicMock()
        self.window._tray_icon.isVisible.return_value = True
        self.window.showMaximized()
        self.app.processEvents()

        self.window.showMinimized()
        deadline = time.time() + 2.0
        while time.time() < deadline and not self.window.isHidden():
            self.app.processEvents()
            time.sleep(0.01)

        self.assertTrue(self.window.isHidden(), "the window did not go to the tray")
        self.assertEqual(
            self.window._tray_restore_state, Qt.WindowState.WindowMaximized
        )


if __name__ == "__main__":
    unittest.main()
