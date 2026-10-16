from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from ksnip_py.capture import MagnifyingGlass, apply_generic_wayland_scaling, portal_result_path
from PyQt6.QtCore import QPoint, QRect


def _application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_portal_result_path_decodes_unicode_file_uri() -> None:
    assert portal_result_path("file:///home/wachin/Im%C3%A1genes/captura.png") == (
        "/home/wachin/Imágenes/captura.png"
    )


def test_portal_result_path_preserves_plain_local_path() -> None:
    assert portal_result_path("/tmp/captura con tilde á.png") == "/tmp/captura con tilde á.png"


def test_generic_wayland_scaling_sets_dpr_without_resampling() -> None:
    _application()
    pixmap = QPixmap(240, 120)

    result = apply_generic_wayland_scaling(pixmap, True, 1.5)

    assert result.size().width() == 240
    assert result.size().height() == 120
    assert result.devicePixelRatio() == 1.5
    assert result.deviceIndependentSize().width() == 160
    assert result.deviceIndependentSize().height() == 80


def test_generic_wayland_scaling_disabled_preserves_dpr() -> None:
    _application()
    pixmap = QPixmap(80, 40)

    result = apply_generic_wayland_scaling(pixmap, False, 2.0)

    assert result.devicePixelRatio() == 1.0


def test_generic_wayland_scaling_ignores_invalid_ratio() -> None:
    _application()
    pixmap = QPixmap(80, 40)

    apply_generic_wayland_scaling(pixmap, True, 0)

    assert pixmap.devicePixelRatio() == 1.0


def _magnifier() -> MagnifyingGlass:
    _application()
    background = QPixmap(400, 300)
    background.fill()
    return MagnifyingGlass(background)


def test_magnifying_glass_null_without_background() -> None:
    _application()
    magnifier = MagnifyingGlass(QPixmap())

    assert magnifier.is_null()


def test_magnifying_glass_positions_next_to_mouse_by_default() -> None:
    magnifier = _magnifier()
    screen_rect = QRect(0, 0, 1920, 1080)

    magnifier.update(QPoint(500, 400), screen_rect)

    assert magnifier._visible_rect.topLeft() == QPoint(520, 420)


def test_magnifying_glass_flips_inside_screen_edges() -> None:
    magnifier = _magnifier()
    screen_rect = QRect(0, 0, 800, 600)

    # Bottom-left corner: place the lens to the top-right of the mouse.
    magnifier.update(QPoint(50, 550), screen_rect)
    assert magnifier._visible_rect.right() <= screen_rect.width()
    assert magnifier._visible_rect.bottom() <= screen_rect.height()

    # Top-right corner: place the lens to the bottom-left of the mouse.
    magnifier.update(QPoint(750, 30), screen_rect)
    assert magnifier._visible_rect.left() >= 0
    assert magnifier._visible_rect.top() >= 0


def test_magnifying_glass_zooms_background_around_mouse() -> None:
    magnifier = _magnifier()

    magnifier.update(QPoint(200, 150), QRect(0, 0, 400, 300))

    assert magnifier._image.size() == magnifier._visible_rect.size()
    assert not magnifier._image.isNull()


def test_magnifying_glass_paints_without_errors() -> None:
    magnifier = _magnifier()
    magnifier.update(QPoint(100, 100), QRect(0, 0, 400, 300))
    target = QPixmap(400, 300)
    target.fill()

    painter = QPainter(target)
    magnifier.paint(painter)
    painter.end()

    assert not target.isNull()


def test_selection_overlay_tracks_mouse_without_buttons_pressed() -> None:
    _application()
    desktop = QPixmap(400, 300)
    desktop.fill()

    overlay = SelectionOverlay(desktop, magnifier_enabled=True)

    assert overlay.hasMouseTracking()
