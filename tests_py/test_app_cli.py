from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from ksnip_py.app import apply_startup_request, build_argument_parser


class _Settings:
    def __init__(self, default_mode: str = "rect") -> None:
        self.default_mode = default_mode

    def value(self, key: str, default=None):
        if key == "capture/default_mode":
            return self.default_mode
        return default


class CommandLineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = build_argument_parser()

    def _window(self) -> MagicMock:
        window = MagicMock()
        window._settings = _Settings()
        window._setting_bool.return_value = False
        return window

    def test_cpp_capture_option_aliases_map_to_expected_modes(self) -> None:
        aliases = {
            "-r": "rect", "--rectarea": "rect",
            "-l": "last_rect", "--lastrectarea": "last_rect",
            "-f": "full", "--fullscreen": "full",
            "-m": "current", "--current": "current",
            "-a": "active", "--active": "active",
            "-u": "under_cursor", "--windowundercursor": "under_cursor",
            "-t": "portal", "--portal": "portal",
        }
        for option, expected in aliases.items():
            with self.subTest(option=option):
                self.assertEqual(self.parser.parse_args([option]).capture_mode, expected)

    def test_cpp_default_options_and_python_language_extension_parse(self) -> None:
        arguments = self.parser.parse_args([
            "--delay", "3", "--cursor", "--save", "--saveto", "/tmp/a.png",
            "--upload", "--language", "es_EC",
        ])
        self.assertEqual(arguments.delay, 3)
        self.assertTrue(arguments.cursor)
        self.assertTrue(arguments.save)
        self.assertEqual(arguments.saveto, "/tmp/a.png")
        self.assertTrue(arguments.upload)
        self.assertEqual(arguments.language, "es_EC")

    def test_negative_delay_and_ambiguous_capture_modes_are_rejected(self) -> None:
        with patch.object(self.parser, "error", side_effect=ValueError):
            with self.assertRaises(ValueError):
                self.parser.parse_args(["--delay", "-1"])
            with self.assertRaises(ValueError):
                self.parser.parse_args(["--fullscreen", "--current"])

    def test_edit_and_positional_image_are_exposed(self) -> None:
        self.assertEqual(self.parser.parse_args(["picture.png"]).image, "picture.png")
        self.assertEqual(self.parser.parse_args(["--edit", "picture.png"]).edit, "picture.png")
        self.assertEqual(self.parser.parse_args(["--edit", "-"]).edit, "-")

    def test_each_capture_mode_dispatches_to_the_corresponding_method(self) -> None:
        methods = {
            "rect": "capture_rect_area",
            "last_rect": "capture_last_rect_area",
            "full": "capture_fullscreen",
            "current": "capture_current_screen",
            "active": "capture_active_window",
            "under_cursor": "capture_window_under_cursor",
            "portal": "capture_portal",
        }
        for mode, method_name in methods.items():
            with self.subTest(mode=mode):
                window = self._window()
                arguments = self.parser.parse_args([f"--{self._long_option(mode)}"])
                with patch("ksnip_py.app.QTimer.singleShot") as single_shot:
                    self.assertTrue(apply_startup_request(window, arguments))
                single_shot.assert_called_once_with(0, getattr(window, method_name))

    @staticmethod
    def _long_option(mode: str) -> str:
        return {
            "rect": "rectarea", "last_rect": "lastrectarea", "full": "fullscreen",
            "current": "current", "active": "active", "under_cursor": "windowundercursor",
            "portal": "portal",
        }[mode]

    def test_direct_save_without_mode_uses_configured_default(self) -> None:
        window = self._window()
        window._settings = _Settings("current")
        arguments = self.parser.parse_args(["--saveto", "/tmp/capture.png", "--cursor"])
        with patch("ksnip_py.app.QTimer.singleShot") as single_shot:
            apply_startup_request(window, arguments)
        self.assertTrue(window._cli_direct_save)
        self.assertEqual(window._cli_save_path, "/tmp/capture.png")
        self.assertTrue(window._capture_cursor_override)
        self.assertTrue(window._quit_after_capture)
        single_shot.assert_called_once_with(0, window.capture_current_screen)

    def test_standard_input_image_bytes_are_opened_directly(self) -> None:
        window = self._window()
        payload = b"image bytes"
        arguments = self.parser.parse_args(["--edit", "-"])
        window._open_image_data.return_value = True
        self.assertTrue(apply_startup_request(window, arguments, payload))
        window._open_image_data.assert_called_once_with(payload, "stdin")


if __name__ == "__main__":
    unittest.main()
