"""Packaged action icons: every theme ships the same set and none is flattened.

Run with:  QT_QPA_PLATFORM=offscreen python -m pytest tests_py/test_app_icons.py
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


pytest.importorskip("PyQt6", reason="PyQt6 is a required dependency")

from PyQt6.QtCore import QSize  # noqa: E402
from PyQt6.QtGui import QIcon  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

ICONS = Path(__file__).resolve().parent.parent / "ksnip_py" / "icons"
THEMES = ("light", "dark")
MIN_OPAQUE_PIXELS = 40


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def _opaque_pixels(icon: QIcon, size: int = 32) -> int:
    image = icon.pixmap(QSize(size, size)).toImage()
    if image.isNull():
        return 0
    image = image.convertToFormat(image.Format.Format_RGBA8888)
    buffer = image.bits()
    buffer.setsize(image.sizeInBytes())
    data = bytes(buffer)
    return sum(1 for index in range(3, len(data), 4) if data[index] > 32)


def test_both_themes_ship_the_same_icon_names():
    sets = {
        theme: {path.name for path in (ICONS / theme).glob("*.svg")}
        for theme in THEMES
    }
    assert sets["light"] == sets["dark"]
    assert "open.svg" in sets["light"]


@pytest.mark.parametrize("theme", THEMES)
def test_every_packaged_icon_renders_something(application, theme):
    for path in sorted((ICONS / theme).glob("*.svg")):
        icon = QIcon(str(path))
        assert not icon.isNull(), path
        assert _opaque_pixels(icon) >= MIN_OPAQUE_PIXELS, f"{path} renders empty"


def test_enabled_icons_keep_their_colours_in_both_themes(application):
    """A single-colour tint turned system icons into black silhouettes."""

    from ksnip_py.main_window import MainWindow
    from ksnip_py.theme import init_theme_manager

    manager = init_theme_manager(application)
    for theme in THEMES:
        manager.set_mode(theme, emit=False)
        window = MainWindow()
        try:
            enabled, disabled = window._icon_tint_colors()
            assert enabled is None, f"{theme}: enabled icons would be tinted flat"
            assert disabled is not None, f"{theme}: disabled icons need a tint"
            assert not window.open_action.icon().isNull(), theme
        finally:
            window.close()
            window.deleteLater()
            application.processEvents()
