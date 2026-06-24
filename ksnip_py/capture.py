from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QMouseEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


@dataclass
class CaptureResult:
    pixmap: QPixmap
    mode: str


def grab_fullscreen() -> CaptureResult | None:
    desktop = _grab_virtual_desktop()
    if desktop.isNull():
        return None
    return CaptureResult(desktop, "full-screen")


def grab_current_screen() -> CaptureResult | None:
    screen = QGuiApplication.screenAt(QCursor.pos())
    if screen is None:
        screen = QApplication.primaryScreen()
    if screen is None:
        return None
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        return None
    return CaptureResult(pixmap, "current-screen")


def grab_active_window() -> CaptureResult | None:
    window_id = _x11_active_window_id()
    if window_id is None:
        return None
    pixmap = _grab_x11_window(window_id)
    if pixmap.isNull():
        return None
    return CaptureResult(pixmap, "active-window")


def grab_window_under_cursor() -> CaptureResult | None:
    window_id = _x11_window_under_cursor_id()
    if window_id is None:
        return None
    pixmap = _grab_x11_window(window_id)
    if pixmap.isNull():
        return None
    return CaptureResult(pixmap, "window-under-cursor")


def grab_rectangular_area(parent: QWidget | None = None) -> CaptureResult | None:
    desktop = _grab_virtual_desktop()
    if desktop.isNull():
        return None
    overlay = SelectionOverlay(desktop)
    overlay.setParent(parent)
    overlay.show()
    overlay.raise_()
    overlay.activateWindow()
    if overlay.wait_for_selection():
        rect = overlay.selected_rect()
        if rect is not None and not rect.isNull():
            return CaptureResult(desktop.copy(rect), "rect-area")
    return None


def _grab_virtual_desktop() -> QPixmap:
    screens = QApplication.screens()
    if not screens:
        return QPixmap()
    virtual_geometry = screens[0].virtualGeometry()
    composed = QPixmap(virtual_geometry.size())
    composed.fill(Qt.GlobalColor.transparent)
    painter = QPainter(composed)
    for screen in screens:
        pixmap = screen.grabWindow(0)
        top_left = screen.geometry().topLeft() - virtual_geometry.topLeft()
        painter.drawPixmap(top_left, pixmap)
    painter.end()
    return composed


def _grab_x11_window(window_id: int) -> QPixmap:
    geometry = _x11_window_geometry(window_id)
    if geometry is None or geometry.isNull():
        return QPixmap()
    desktop = _grab_virtual_desktop()
    if desktop.isNull():
        return QPixmap()
    virtual_geometry = QApplication.screens()[0].virtualGeometry()
    relative_rect = geometry.translated(-virtual_geometry.topLeft())
    return desktop.copy(relative_rect)


def _x11_active_window_id() -> int | None:
    output = _run_capture_helper(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
    if not output:
        return None
    match = re.search(r"window id # (0x[0-9a-fA-F]+)", output)
    if match is None:
        return None
    window_id = int(match.group(1), 16)
    return window_id or None


def _x11_window_under_cursor_id() -> int | None:
    output = _run_capture_helper(["xdotool", "getmouselocation", "--shell"])
    if not output:
        return None
    match = re.search(r"^WINDOW=(\d+)$", output, re.MULTILINE)
    if match is None:
        return None
    window_id = int(match.group(1))
    return window_id or None


def _x11_window_geometry(window_id: int) -> QRect | None:
    output = _run_capture_helper(["xwininfo", "-id", str(window_id)])
    if not output:
        return None

    def _find(pattern: str) -> int | None:
        match = re.search(pattern, output, re.MULTILINE)
        return int(match.group(1)) if match is not None else None

    x = _find(r"Absolute upper-left X:\s+(-?\d+)")
    y = _find(r"Absolute upper-left Y:\s+(-?\d+)")
    width = _find(r"Width:\s+(\d+)")
    height = _find(r"Height:\s+(\d+)")
    if None in (x, y, width, height):
        return None
    return QRect(x, y, width, height)


def _run_capture_helper(command: list[str]) -> str | None:
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


class SelectionOverlay(QWidget):
    selection_completed = pyqtSignal()

    def __init__(self, desktop: QPixmap) -> None:
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self._desktop = desktop
        self._origin = QPoint()
        self._current = QPoint()
        self._dragging = False
        self._accepted = False
        self._virtual_geometry = QApplication.screens()[0].virtualGeometry()
        self.setGeometry(self._virtual_geometry)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def wait_for_selection(self) -> bool:
        loop = QApplication.instance()
        while self.isVisible():
            loop.processEvents()
        return self._accepted

    def selected_rect(self) -> QRect | None:
        if not self._accepted:
            return None
        rect = QRect(self._origin, self._current).normalized()
        return rect

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._desktop)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        if self._dragging or self._accepted:
            rect = QRect(self._origin, self._current).normalized()
            painter.drawPixmap(rect, self._desktop, rect)
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawRect(rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            self.close()
            return
        self._origin = event.position().toPoint()
        self._current = self._origin
        self._dragging = True
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._dragging:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._current = event.position().toPoint()
            self._dragging = False
            self._accepted = True
        self.close()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self._accepted = False
            self.close()
