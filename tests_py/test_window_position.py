from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest import mock

from PyQt6.QtCore import QEvent, QPoint, QRect, QSettings
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
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
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


class _FakeScreen:
    """Minimal stand-in for QScreen used to simulate monitor layouts."""

    def __init__(self, geometry: QRect) -> None:
        self._geometry = geometry

    def availableGeometry(self) -> QRect:
        return self._geometry


class _ScreensProxy:
    """Stands in for QGuiApplication but only overrides the screen list."""

    def __init__(self, rects) -> None:
        self._rects = rects

    def screens(self):
        return [_FakeScreen(rect) for rect in self._rects]

    def __getattr__(self, name):
        return getattr(QGuiApplication, name)


def _fake_screens(*rects: QRect):
    return mock.patch("ksnip_py.main_window.QGuiApplication", _ScreensProxy(rects))


class MultiMonitorPositionTest(unittest.TestCase):
    """Clamping against layouts that cannot be reproduced on the test host."""

    PRIMARY = QRect(0, 0, 1366, 768)
    RIGHT = QRect(1366, 0, 1920, 1080)
    LEFT = QRect(-1920, 0, 1920, 1080)

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("multi-monitor-test")
        QSettings().clear()
        self.window = MainWindow()
        self.window.resize(400, 300)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def clamp(self, point, *rects):
        with _fake_screens(*rects):
            return self.window._clamp_position_to_screens(point)

    def test_position_on_secondary_monitor_is_kept(self):
        self.assertEqual(self.clamp(QPoint(1500, 300), self.PRIMARY, self.RIGHT), QPoint(1500, 300))

    def test_position_on_left_monitor_keeps_negative_coordinates(self):
        self.assertEqual(self.clamp(QPoint(-1800, 200), self.LEFT, self.PRIMARY), QPoint(-1800, 200))

    def test_position_on_disconnected_monitor_centers_the_window(self):
        # Saved while a third monitor was attached; it is gone now.
        self.assertIsNone(self.clamp(QPoint(3400, 900), self.PRIMARY))

    def test_window_dragged_past_the_secondary_edge_is_clamped_back(self):
        target = self.clamp(QPoint(3000, 900), self.PRIMARY, self.RIGHT)
        self.assertEqual(target.x(), self.RIGHT.right() - 400 + 1)
        self.assertEqual(target.y(), self.RIGHT.bottom() - 300 + 1)

    def test_straddling_window_stays_on_the_monitor_holding_its_title_bar(self):
        # The point is on the primary screen, so the window is pulled back onto
        # it instead of jumping to the monitor that covers more of the window.
        target = self.clamp(QPoint(1200, 100), self.PRIMARY, self.RIGHT)
        self.assertEqual(target.x(), self.PRIMARY.right() - 400 + 1)

    def test_window_hanging_off_the_bottom_stays_on_its_monitor(self):
        # Remembered near the bottom edge of the external monitor; the window
        # must stay there instead of jumping to the primary screen.
        target = self.clamp(QPoint(2500, 1000), self.PRIMARY, self.RIGHT)
        self.assertEqual(target.x(), 2500)
        self.assertEqual(target.y(), self.RIGHT.bottom() - 300 + 1)

    def test_restored_position_lands_on_the_secondary_monitor(self):
        self.window.close()
        self.window._settings.setValue("window/position", "2000,400")
        window = MainWindow()
        with _fake_screens(self.PRIMARY, self.RIGHT):
            window.show()
            self.assertEqual(window.pos(), QPoint(2000, 400))
            self.assertEqual(window._settings.value("window/position"), "2000,400")
        window.close()


class DecorationShiftTest(unittest.TestCase):
    """The window manager shifts the first placement by the frame margins."""

    def setUp(self):
        self.app = QApplication.instance() or QApplication([])
        self._previous_org = self.app.organizationName()
        self._previous_app = self.app.applicationName()
        self.app.setOrganizationName("ksnip-pyqt6-tests")
        self.app.setApplicationName("decoration-shift-test")
        QSettings().clear()
        self.window = MainWindow()
        self.window.show()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QSettings().clear()
        self.app.setOrganizationName(self._previous_org)
        self.app.setApplicationName(self._previous_app)

    def test_place_window_records_the_requested_position(self):
        self.window._place_window(QPoint(300, 200))
        self.assertEqual(self.window._pending_position, QPoint(300, 200))

    def test_decoration_shift_is_corrected(self):
        self.window._place_window(QPoint(300, 200))
        # The window manager placed the frame at the requested point, so the
        # client area sits one border and one title bar away from it.
        self.window.move(299, 174)
        self.window._apply_position_fix()
        self.assertEqual(self.window.pos(), QPoint(300, 200))

    def test_correction_stops_once_the_position_holds(self):
        self.window._place_window(QPoint(300, 200))
        self.window.move(299, 174)
        for _ in range(4):
            self.window._apply_position_fix()
        self.assertEqual(self.window.pos(), QPoint(300, 200))
        self.assertIsNone(self.window._pending_position)
        self.assertFalse(self.window._position_fix_timer.isActive())

    def test_large_move_is_left_alone(self):
        self.window._place_window(QPoint(300, 200))
        self.window.move(100, 100)
        self.window._apply_position_fix()
        self.assertEqual(self.window.pos(), QPoint(100, 100))
        self.assertIsNone(self.window._pending_position)


if __name__ == "__main__":
    unittest.main()
