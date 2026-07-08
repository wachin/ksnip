from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("ksnip")
    app.setOrganizationDomain("ksnip.ksnip.org")
    app.setApplicationName("ksnip-pyqt6")
    app.setApplicationVersion("0.1.0")
    app_icon_path = Path(__file__).resolve().parent / "icons" / "ksnip.svg"
    if app_icon_path.exists():
        app.setWindowIcon(QIcon(str(app_icon_path)))

    window = MainWindow()
    if window._setting_bool("tray/start_minimized", False) and window._tray_icon is not None and window._tray_icon.isVisible():
        window.hide()
    else:
        window.show()
    return app.exec()
