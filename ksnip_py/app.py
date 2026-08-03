from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def _non_negative_int(value: str) -> int:
    resolved = int(value)
    if resolved < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return resolved


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ksnip-pyqt6", description="Ksnip Screenshot Tool")
    parser.add_argument("image", nargs="?", help="Edit an existing image in ksnip")
    parser.add_argument("-e", "--edit", metavar="IMAGE", help="Edit an existing image in ksnip")
    capture_modes = parser.add_mutually_exclusive_group()
    capture_modes.add_argument("-r", "--rectarea", action="store_const", const="rect", dest="capture_mode", help="Capture a rectangular area")
    capture_modes.add_argument("-l", "--lastrectarea", action="store_const", const="last_rect", dest="capture_mode", help="Capture the last rectangular area")
    capture_modes.add_argument("-f", "--fullscreen", action="store_const", const="full", dest="capture_mode", help="Capture all screens")
    capture_modes.add_argument("-m", "--current", action="store_const", const="current", dest="capture_mode", help="Capture the current screen")
    capture_modes.add_argument("-a", "--active", action="store_const", const="active", dest="capture_mode", help="Capture the active window")
    capture_modes.add_argument("-u", "--windowundercursor", action="store_const", const="under_cursor", dest="capture_mode", help="Capture the window under the cursor")
    parser.add_argument("-d", "--delay", type=_non_negative_int, default=None, metavar="SECONDS")
    parser.add_argument("-c", "--cursor", action="store_true", help="Include the mouse cursor in the screenshot")
    parser.add_argument("-s", "--save", action="store_true", help="Save a screenshot to the configured default location without opening the editor")
    parser.add_argument("-p", "--saveto", metavar="PATH", help="Save a screenshot to PATH without opening the editor")
    parser.add_argument("-v", "--version", action="version", version="ksnip-pyqt6 0.1.0")
    return parser


def apply_startup_request(window: MainWindow, arguments: argparse.Namespace) -> bool:
    image_path = arguments.image or arguments.edit
    if image_path:
        return window._open_image_path(str(Path(image_path).expanduser()))
    if arguments.delay is not None:
        window._capture_delay_override_seconds = arguments.delay
    command_line_capture = arguments.capture_mode is not None or arguments.save or arguments.saveto
    if command_line_capture:
        window._capture_cursor_override = arguments.cursor
    if arguments.save or arguments.saveto:
        window._cli_direct_save = True
        window._cli_save_path = arguments.saveto
        window._quit_after_capture = True
    capture_methods = {
        "rect": window.capture_rect_area,
        "last_rect": window.capture_last_rect_area,
        "full": window.capture_fullscreen,
        "current": window.capture_current_screen,
        "active": window.capture_active_window,
        "under_cursor": window.capture_window_under_cursor,
    }
    requested_mode = arguments.capture_mode
    if requested_mode is None and (arguments.save or arguments.saveto):
        requested_mode = str(window._settings.value("capture/default_mode", "rect"))
    capture_method = capture_methods.get(requested_mode)
    if capture_method is not None:
        QTimer.singleShot(0, capture_method)
    elif window._setting_bool("application/capture_on_startup", False):
        default_mode = str(window._settings.value("capture/default_mode", "rect"))
        QTimer.singleShot(0, capture_methods.get(default_mode, window.capture_rect_area))
    return True


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if arguments.image and arguments.edit:
        parser.error("use either IMAGE or --edit, not both")

    app = QApplication([sys.argv[0]])
    app.setOrganizationName("ksnip")
    app.setOrganizationDomain("ksnip.ksnip.org")
    app.setApplicationName("ksnip-pyqt6")
    app.setApplicationVersion("0.1.0")
    app_icon_path = Path(__file__).resolve().parent / "icons" / "ksnip.svg"
    if app_icon_path.exists():
        app.setWindowIcon(QIcon(str(app_icon_path)))

    window = MainWindow()
    if not apply_startup_request(window, arguments):
        return 1
    if window._quit_after_capture:
        window.hide()
    elif window._setting_bool("tray/start_minimized", False) and window._tray_icon is not None and window._tray_icon.isVisible():
        window.hide()
    else:
        window.show()
    return app.exec()
