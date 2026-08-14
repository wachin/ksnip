from __future__ import annotations

import ctypes
import ctypes.util
import math
import os
import re
import subprocess
from dataclasses import dataclass
from dataclasses import field

from PyQt6.QtCore import QCoreApplication, QEventLoop, QObject, QPoint, QRect, QTimer, Qt, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusObjectPath
from PyQt6.QtGui import QColor, QCursor, QGuiApplication, QImage, QMouseEvent, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget


@dataclass
class CaptureResult:
    pixmap: QPixmap
    mode: str
    global_origin: QPoint = field(default_factory=QPoint)
    cursor_image: QImage | None = None
    cursor_position: QPoint | None = None


_last_rect_area: QRect | None = None
_portal_last_error = ""
_portal_was_canceled = False


def desktop_environment() -> str:
    return next(
        (
            value
            for value in (
                os.environ.get("XDG_CURRENT_DESKTOP", ""),
                os.environ.get("XDG_SESSION_DESKTOP", ""),
                os.environ.get("DESKTOP_SESSION", ""),
            )
            if value
        ),
        "unknown",
    )


def is_wayland_session() -> bool:
    platform_name = QGuiApplication.platformName().lower() if QGuiApplication.instance() is not None else ""
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    return platform_name.startswith("wayland") or session_type == "wayland"


def recommended_portal_backend(desktop: str | None = None) -> str:
    normalized = (desktop or desktop_environment()).lower()
    mappings = (
        (("kde", "plasma"), "xdg-desktop-portal-kde"),
        (("lxqt",), "xdg-desktop-portal-lxqt"),
        (("phosh",), "xdg-desktop-portal-phosh"),
        (("sway", "wayfire", "river", "wlroots"), "xdg-desktop-portal-wlr"),
        (("cinnamon", "x-cinnamon"), "xdg-desktop-portal-xapp"),
        (("gnome", "ubuntu"), "xdg-desktop-portal-gnome"),
    )
    for names, package in mappings:
        if any(name in normalized for name in names):
            return package
    return "xdg-desktop-portal-gtk"


def portal_failure_message() -> str:
    desktop = desktop_environment()
    session_type = os.environ.get("XDG_SESSION_TYPE", "unknown")
    package = recommended_portal_backend(desktop)
    detail = _portal_last_error or QCoreApplication.translate("PortalDiagnostics", "The screenshot portal did not return an image.")
    return (
        f"{QCoreApplication.translate('PortalDiagnostics', 'Portal capture is unavailable: %1').replace('%1', detail)}\n\n"
        f"{QCoreApplication.translate('PortalDiagnostics', 'Detected desktop: %1').replace('%1', desktop)}\n"
        f"{QCoreApplication.translate('PortalDiagnostics', 'Session type: %1').replace('%1', session_type)}\n\n"
        f"{QCoreApplication.translate('PortalDiagnostics', 'Install the portal frontend and the recommended backend:')}\n"
        f"sudo apt install xdg-desktop-portal {package}\n\n"
        + QCoreApplication.translate(
            "PortalDiagnostics",
            "With Fluxbox, Openbox, IceWM, or another manually assembled session, xdg-desktop-portal-gtk is the usual fallback. The session must export XDG_CURRENT_DESKTOP and may require a matching portals.conf file.",
        )
    )


def portal_capture_was_canceled() -> bool:
    return _portal_was_canceled


def portal_result_path(value: object) -> str:
    """Return a local path from the URI/path supplied by the screenshot portal."""
    source = str(value or "")
    url = QUrl(source)
    return url.toLocalFile() if url.isLocalFile() else source


def apply_generic_wayland_scaling(
    pixmap: QPixmap,
    enabled: bool,
    device_pixel_ratio: float | None = None,
) -> QPixmap:
    """Apply Qt high-DPI metadata without resampling the portal image.

    The generic portal does not report which monitor produced the image.  As
    in the C++ implementation, the primary screen DPR is therefore used when
    no explicit ratio is supplied.
    """
    if not enabled or pixmap.isNull():
        return pixmap
    if device_pixel_ratio is None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return pixmap
        device_pixel_ratio = screen.devicePixelRatio()
    ratio = float(device_pixel_ratio)
    if math.isfinite(ratio) and ratio > 0:
        pixmap.setDevicePixelRatio(ratio)
    return pixmap


def grab_fullscreen() -> CaptureResult | None:
    desktop = _grab_virtual_desktop()
    if desktop.isNull():
        return None
    return CaptureResult(desktop, "full-screen", QApplication.screens()[0].virtualGeometry().topLeft())


def grab_current_screen() -> CaptureResult | None:
    screen = QGuiApplication.screenAt(QCursor.pos())
    if screen is None:
        screen = QApplication.primaryScreen()
    if screen is None:
        return None
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        return None
    return CaptureResult(pixmap, "current-screen", screen.geometry().topLeft())


def grab_active_window() -> CaptureResult | None:
    window_id = _x11_active_window_id()
    if window_id is None:
        return None
    pixmap = _grab_x11_window(window_id)
    if pixmap.isNull():
        return None
    geometry = _x11_window_geometry(window_id)
    return CaptureResult(pixmap, "active-window", geometry.topLeft() if geometry is not None else QPoint())


def grab_window_under_cursor() -> CaptureResult | None:
    window_id = _x11_window_under_cursor_id()
    if window_id is None:
        return None
    pixmap = _grab_x11_window(window_id)
    if pixmap.isNull():
        return None
    geometry = _x11_window_geometry(window_id)
    return CaptureResult(pixmap, "window-under-cursor", geometry.topLeft() if geometry is not None else QPoint())


class _PortalResponse(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.response_code: int | None = None
        self.results: dict = {}
        self.loop = QEventLoop()

    @pyqtSlot("uint", "QVariantMap")
    def receive(self, response_code: int, results: dict) -> None:
        self.response_code = response_code
        self.results = results
        self.loop.quit()


def grab_portal(*, interactive: bool = True, scale: bool = False) -> CaptureResult | None:
    global _portal_last_error, _portal_was_canceled
    _portal_last_error = ""
    _portal_was_canceled = False
    connection = QDBusConnection.sessionBus()
    if not connection.isConnected():
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "the D-Bus session bus is not available.")
        return None
    interface = QDBusInterface(
        "org.freedesktop.portal.Desktop",
        "/org/freedesktop/portal/desktop",
        "org.freedesktop.portal.Screenshot",
        connection,
    )
    if not interface.isValid():
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "the xdg-desktop-portal service is not available.")
        return None
    token = f"ksnip_py_{id(interface):x}"
    reply = interface.call("Screenshot", "", {"interactive": interactive, "handle_token": token})
    if reply.type() == QDBusMessage.MessageType.ErrorMessage or not reply.arguments():
        _portal_last_error = reply.errorMessage() or QCoreApplication.translate("PortalDiagnostics", "the Screenshot portal interface is unavailable.")
        return None
    request = reply.arguments()[0]
    request_path = request.path() if isinstance(request, QDBusObjectPath) else str(request)
    if not request_path:
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "the portal returned an invalid request path.")
        return None

    response = _PortalResponse()
    connected = connection.connect(
        "",
        request_path,
        "org.freedesktop.portal.Request",
        "Response",
        response.receive,
    )
    if not connected:
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "ksnip could not subscribe to the portal response.")
        return None
    timeout = QTimer(response)
    timeout.setSingleShot(True)
    timeout.timeout.connect(response.loop.quit)
    timeout.start(120_000)
    response.loop.exec()
    connection.disconnect(
        "",
        request_path,
        "org.freedesktop.portal.Request",
        "Response",
        response.receive,
    )
    if response.response_code is None:
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "the portal response timed out.")
        return None
    if response.response_code != 0:
        _portal_was_canceled = response.response_code == 1
        _portal_last_error = (
            QCoreApplication.translate("PortalDiagnostics", "capture was canceled.")
            if _portal_was_canceled
            else QCoreApplication.translate("PortalDiagnostics", "portal error code %1.").replace("%1", str(response.response_code))
        )
        return None
    path = portal_result_path(response.results.get("uri") or response.results.get("path"))
    image = QImage(path)
    if image.isNull():
        source = path or QCoreApplication.translate("PortalDiagnostics", "an empty path")
        _portal_last_error = QCoreApplication.translate("PortalDiagnostics", "the returned image could not be loaded from %1.").replace("%1", source)
        return None
    pixmap = apply_generic_wayland_scaling(QPixmap.fromImage(image), scale)
    return CaptureResult(pixmap, "portal")


def grab_rectangular_area(parent: QWidget | None = None) -> CaptureResult | None:
    global _last_rect_area
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
            _last_rect_area = QRect(rect)
            origin = QApplication.screens()[0].virtualGeometry().topLeft() + rect.topLeft()
            return CaptureResult(desktop.copy(rect), "rect-area", origin)
    return None


def has_last_rectangular_area() -> bool:
    return _last_rect_area is not None and not _last_rect_area.isNull()


def grab_last_rectangular_area() -> CaptureResult | None:
    if not has_last_rectangular_area():
        return None
    desktop = _grab_virtual_desktop()
    if desktop.isNull():
        return None
    rect = QRect(_last_rect_area)
    rect = rect.intersected(QRect(QPoint(0, 0), desktop.size()))
    if rect.isNull() or rect.isEmpty():
        return None
    origin = QApplication.screens()[0].virtualGeometry().topLeft() + rect.topLeft()
    return CaptureResult(desktop.copy(rect), "last-rect-area", origin)


class _XFixesCursorImage(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_short),
        ("y", ctypes.c_short),
        ("width", ctypes.c_ushort),
        ("height", ctypes.c_ushort),
        ("xhot", ctypes.c_ushort),
        ("yhot", ctypes.c_ushort),
        ("cursor_serial", ctypes.c_ulong),
        ("pixels", ctypes.POINTER(ctypes.c_ulong)),
        ("atom", ctypes.c_ulong),
        ("name", ctypes.c_char_p),
    ]


def grab_x11_cursor() -> tuple[QImage, QPoint] | None:
    x11_name = ctypes.util.find_library("X11")
    xfixes_name = ctypes.util.find_library("Xfixes")
    if not x11_name or not xfixes_name:
        return None
    try:
        x11 = ctypes.CDLL(x11_name)
        xfixes = ctypes.CDLL(xfixes_name)
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XFree.argtypes = [ctypes.c_void_p]
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        xfixes.XFixesGetCursorImage.argtypes = [ctypes.c_void_p]
        xfixes.XFixesGetCursorImage.restype = ctypes.POINTER(_XFixesCursorImage)
        display = x11.XOpenDisplay(None)
        if not display:
            return None
        cursor_ptr = xfixes.XFixesGetCursorImage(display)
        if not cursor_ptr:
            x11.XCloseDisplay(display)
            return None
        cursor = cursor_ptr.contents
        image = QImage(cursor.width, cursor.height, QImage.Format.Format_ARGB32)
        for y in range(cursor.height):
            for x in range(cursor.width):
                image.setPixel(x, y, int(cursor.pixels[y * cursor.width + x]) & 0xFFFFFFFF)
        top_left = QPoint(cursor.x - cursor.xhot, cursor.y - cursor.yhot)
        x11.XFree(cursor_ptr)
        x11.XCloseDisplay(display)
        return image, top_left
    except (AttributeError, OSError, ValueError):
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
