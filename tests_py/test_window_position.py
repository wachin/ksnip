from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QSettings
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

from ksnip_py.main_window import MainWindow


class WindowPositionTest(unittest.TestCase):
    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("window-position-test")
        QSettings().clear()
        self.window = MainWindow()
        self.settings = self.window._settings

    def tearDown(self):
        self.window.close()
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def _available(self):
        screen = QGuiApplication.primaryScreen()
        self.assertIsNotNone(screen)
        return screen.availableGeometry()

    def test_origin_is_treated_as_unset(self):
        # A window that was never placed reports 0,0; restoring it would put
        # the title bar off-screen, so the window must be centered instead.
        self.assertIsNone(self.window._clamp_position_to_screens(QPoint(0, 0)))

    def test_position_outside_every_screen_is_rejected(self):
        self.assertIsNone(self.window._clamp_position_to_screens(QPoint(-9000, -9000)))

    def test_position_inside_the_screen_is_kept(self):
        available = self._available()
        point = QPoint(available.left() + 40, available.top() + 120)
        if point.x() + self.window.width() > available.right():
            self.skipTest("offscreen screen is narrower than the window")
        self.assertEqual(self.window._clamp_position_to_screens(point), point)

    def test_position_above_the_top_edge_is_clamped(self):
        available = self._available()
        target = self.window._clamp_position_to_screens(QPoint(available.left() + 40, available.top()))
        self.assertIsNotNone(target)
        self.assertEqual(target.y(), available.top() + MainWindow.TITLE_BAR_CLEARANCE)

    def test_position_is_not_saved_before_the_first_show(self):
        self.window._persist_window_position()
        self.assertIsNone(self.settings.value("window/position"))

    def test_position_is_saved_after_the_window_is_shown(self):
        self.window.show()
        self.window.move(150, 120)
        self.window._persist_window_position()
        self.assertEqual(self.settings.value("window/position"), "150,120")

    def test_restored_position_is_clamped_and_stored(self):
        self.window.close()
        self.settings.setValue("window/position", "100,5")
        window = MainWindow()
        window.show()
        available = self._available()
        expected = f"100,{available.top() + MainWindow.TITLE_BAR_CLEARANCE}"
        self.assertEqual(window._settings.value("window/position"), expected)
        window.close()


if __name__ == "__main__":
    unittest.main()
