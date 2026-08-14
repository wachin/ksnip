from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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


if __name__ == "__main__":
    unittest.main()
