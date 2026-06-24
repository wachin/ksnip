from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("ksnip")
    app.setOrganizationDomain("ksnip.ksnip.org")
    app.setApplicationName("ksnip-pyqt6")
    app.setApplicationVersion("0.1.0")

    window = MainWindow()
    if window._setting_bool("tray/start_minimized", False) and window._tray_icon is not None and window._tray_icon.isVisible():
        window.hide()
    else:
        window.show()
    return app.exec()
