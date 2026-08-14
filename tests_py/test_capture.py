from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from ksnip_py.capture import apply_generic_wayland_scaling, portal_result_path


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
