from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QApplication

from ksnip_py.app import build_argument_parser, should_show_for_remote_request
from ksnip_py.main_window import MainWindow
from ksnip_py.single_instance import SingleInstanceController


APP = QApplication.instance() or QApplication([])


class StartupLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = build_argument_parser()

    def test_remote_edit_and_plain_invocation_show_editor_but_capture_does_not(self) -> None:
        self.assertTrue(should_show_for_remote_request(self.parser.parse_args([])))
        self.assertTrue(should_show_for_remote_request(self.parser.parse_args(["picture.png"])))
        self.assertTrue(should_show_for_remote_request(self.parser.parse_args(["--edit", "picture.png"])))
        self.assertFalse(should_show_for_remote_request(self.parser.parse_args(["--fullscreen"])))
        self.assertFalse(should_show_for_remote_request(self.parser.parse_args(["--save"])))
        self.assertFalse(should_show_for_remote_request(self.parser.parse_args(["--upload"])))

    def test_second_listener_does_not_remove_a_live_primary_endpoint(self) -> None:
        controller = SingleInstanceController("ksnip-pyqt6-test")
        controller._server = MagicMock()
        controller._server.listen.return_value = False
        probe = MagicMock()
        probe.waitForConnected.return_value = True

        with (
            patch("ksnip_py.single_instance.QLocalSocket", return_value=probe),
            patch("ksnip_py.single_instance.QLocalServer.removeServer") as remove_server,
        ):
            self.assertFalse(controller.listen(lambda _arguments, _image: None))

        probe.connectToServer.assert_called_once_with("ksnip-pyqt6-test")
        probe.disconnectFromServer.assert_called_once_with()
        remove_server.assert_not_called()

    def test_stale_single_instance_endpoint_is_removed_and_retried(self) -> None:
        controller = SingleInstanceController("ksnip-pyqt6-test")
        controller._server = MagicMock()
        controller._server.listen.side_effect = [False, True]
        probe = MagicMock()
        probe.waitForConnected.return_value = False

        with (
            patch("ksnip_py.single_instance.QLocalSocket", return_value=probe),
            patch("ksnip_py.single_instance.QLocalServer.removeServer") as remove_server,
        ):
            self.assertTrue(controller.listen(lambda _arguments, _image: None))

        remove_server.assert_called_once_with("ksnip-pyqt6-test")
        self.assertEqual(controller._server.listen.call_count, 2)

    def test_quit_cancel_keeps_application_and_tray_alive(self) -> None:
        window = MagicMock()
        window._allow_quit = False
        window.close.return_value = False
        window._tray_icon = MagicMock()

        with patch("ksnip_py.main_window.QGuiApplication.instance") as instance:
            MainWindow.quit_application(window)

        self.assertFalse(window._allow_quit)
        window._tray_icon.hide.assert_not_called()
        instance.assert_not_called()

    def test_confirmed_quit_hides_tray_and_exits_application(self) -> None:
        window = MagicMock()
        window._allow_quit = False
        window.close.return_value = True
        window._tray_icon = MagicMock()
        application = MagicMock()

        with patch("ksnip_py.main_window.QGuiApplication.instance", return_value=application):
            MainWindow.quit_application(window)

        self.assertTrue(window._allow_quit)
        window._tray_icon.hide.assert_called_once_with()
        application.quit.assert_called_once_with()


class TrayBehaviorTest(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_org = APP.organizationName()
        self._previous_app = APP.applicationName()
        APP.setOrganizationName("ksnip-pyqt6-tests")
        APP.setApplicationName("tray-behavior-test")
        from PyQt6.QtCore import QSettings

        QSettings().clear()

    def tearDown(self) -> None:
        from PyQt6.QtCore import QSettings

        QSettings().clear()
        APP.setOrganizationName(self._previous_org)
        APP.setApplicationName(self._previous_app)

    def _window_with_visible_tray(self) -> MainWindow:
        window = MainWindow()
        if window._tray_icon is None:
            window._tray_icon = MagicMock()
        window._tray_icon.isVisible = MagicMock(return_value=True)
        return window

    def test_first_show_centers_window_with_title_bar_clearance(self) -> None:
        window = self._window_with_visible_tray()
        window.show()
        APP.processEvents()

        available = APP.primaryScreen().availableGeometry()
        position = window.pos()

        # The client window must leave room for the WM title bar above it.
        self.assertGreaterEqual(position.y(), available.top() + MainWindow.TITLE_BAR_CLEARANCE - 1)
        self.assertLess(position.x() + window.width(), available.right())

    def test_second_show_keeps_position(self) -> None:
        window = self._window_with_visible_tray()
        window.show()
        APP.processEvents()
        first_position = window.pos()

        window.hide()
        window.show()
        APP.processEvents()

        self.assertEqual(window.pos(), first_position)

    def test_minimize_to_tray_clears_minimized_state(self) -> None:
        # Fluxbox leaves a ghost empty frame when an iconified window is
        # withdrawn; hide_to_tray must normalize the state first.
        window = self._window_with_visible_tray()
        window.show()
        APP.processEvents()

        window.setWindowState(Qt.WindowState.WindowMinimized)
        APP.processEvents()

        self.assertFalse(window.isVisible())
        self.assertFalse(window.isMinimized())
        self.assertEqual(
            window.windowState() & Qt.WindowState.WindowMinimized,
            Qt.WindowState.WindowNoState,
        )

    def test_minimize_hint_is_shown_only_once(self) -> None:
        window = self._window_with_visible_tray()

        # First call returns the hint message and persists the flag.
        self.assertEqual(window._first_time_tray_message("first"), "first")
        self.assertTrue(window._setting_bool("tray/hint_shown", False))
        # Every later call suppresses the message: the user already knows
        # where the tray icon lives.
        self.assertIsNone(window._first_time_tray_message("second"))
        self.assertIsNone(window._first_time_tray_message("third"))

    def test_restore_from_tray_survives_spurious_minimize_state_change(self) -> None:
        from PyQt6.QtCore import QEvent

        window = self._window_with_visible_tray()
        window.show()
        APP.processEvents()

        window.show_from_tray()
        APP.processEvents()

        # The restore completes and the guard is released afterwards.
        self.assertTrue(window.isVisible())
        self.assertFalse(window._restoring_from_tray)

        # A transient WindowStateChange arriving while restoring (common on
        # some window managers) must not re-hide the freshly restored window.
        with patch.object(window, "hide_to_tray") as hide_to_tray:
            window._restoring_from_tray = True
            window.changeEvent(QEvent(QEvent.Type.WindowStateChange))
            self.assertFalse(hide_to_tray.called)


if __name__ == "__main__":
    unittest.main()
