"""Version-independent check: disabled menu items are drawn in solid #5c5c5c.

Run with:  QT_QPA_PLATFORM=offscreen python -m pytest tests_py/test_disabled_menu_style.py
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QProxyStyle, QStyle, QStyleFactory, QStyleOptionMenuItem

from ksnip_py.menu_style import SolidDisabledMenuStyle

GRAY = QColor("#5c5c5c")
TOL = 3


class _EtchedDisabledStyle(QProxyStyle):
    """Test double reproducing the bug: disabled text gets a light 1px copy."""

    def drawControl(self, element, option, painter, widget=None):  # noqa: N802
        if (
            element == QStyle.ControlElement.CE_MenuItem
            and isinstance(option, QStyleOptionMenuItem)
            and option.menuItemType == QStyleOptionMenuItem.MenuItemType.Normal
            and not (option.state & QStyle.StateFlag.State_Enabled)
        ):
            painter.save()
            painter.setPen(QColor("#f5f5f5"))
            painter.setFont(option.font)
            painter.drawText(option.rect.adjusted(37, 1, 0, 1), int(Qt.AlignmentFlag.AlignVCenter), option.text)
            painter.restore()
        super().drawControl(element, option, painter, widget)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def _icon() -> QIcon:
    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.fillRect(4, 4, 24, 24, QColor("#f2f2f2"))
    p.end()
    return QIcon(pm)


def _dark(app):
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#353535"))
    pal.setColor(QPalette.ColorRole.Button, QColor("#353535"))
    pal.setColor(QPalette.ColorRole.Base, QColor("#232323"))
    pal.setColor(QPalette.ColorRole.Light, QColor("#ffffff"))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        pal.setColor(role, QColor("#f2f2f2"))
        pal.setColor(QPalette.ColorGroup.Disabled, role, GRAY)
    app.setPalette(pal)


def _render(app, style, with_enabled=False):
    app.setStyle(style)
    _dark(app)
    menu = QMenu()
    on, off = QAction(_icon(), "Open", menu), QAction(_icon(), "Save as", menu)
    off.setEnabled(False)
    sub = menu.addMenu("Recent")  # disabled sub-menu (empty)
    sub.setEnabled(False)
    menu.addAction(on)
    menu.addAction(off)
    menu.ensurePolished()
    menu.resize(menu.sizeHint())
    menu.show()
    app.processEvents()
    if with_enabled:
        return menu.grab().toImage(), menu.actionGeometry(on)
    return menu.grab().toImage(), menu.actionGeometry(off), menu.actionGeometry(sub.menuAction())


def _bg(image, rect):
    return QColor(image.pixel(rect.left() + 1, rect.top() + 1))


def _assert_only_bg_to_gray(image, rect):
    """Every pixel must be a mix of the background and #5c5c5c, and some pixels
    must be (nearly) exactly #5c5c5c: no light shadow, no white text."""
    bg, seen_solid = _bg(image, rect), False
    for y in range(rect.top() + 1, rect.bottom() - 1):
        for x in range(rect.left() + 3, rect.right() - 3):
            c = QColor(image.pixel(x, y))
            for a, b, g in ((c.red(), bg.red(), GRAY.red()), (c.green(), bg.green(), GRAY.green()), (c.blue(), bg.blue(), GRAY.blue())):
                assert min(b, g) - TOL <= a <= max(b, g) + TOL, f"pixel {x},{y} = {c.name()} outside {bg.name()}..{GRAY.name()}"
            seen_solid |= all(abs(c.red() - GRAY.red()) <= TOL and abs(c.green() - GRAY.green()) <= TOL for _ in (0,))
    assert seen_solid, "no solid #5c5c5c pixel found in the disabled item"


@pytest.mark.parametrize("name", [n for n in ("Fusion", "Windows") if n in QStyleFactory.keys()])
def test_disabled_items_are_solid_gray_with_any_base_style(app, name):
    image, off, sub = _render(app, SolidDisabledMenuStyle(QStyleFactory.create(name)))
    _assert_only_bg_to_gray(image, off)
    _assert_only_bg_to_gray(image, sub)  # sub-menu arrow too


def test_etched_base_style_is_neutralised(app):
    etched = _EtchedDisabledStyle(QStyleFactory.create("Fusion"))
    broken, off, _ = _render(app, etched)
    with pytest.raises(AssertionError):  # the test double really reproduces the bug
        _assert_only_bg_to_gray(broken, off)
    fixed, off, _ = _render(app, SolidDisabledMenuStyle(_EtchedDisabledStyle(QStyleFactory.create("Fusion"))))
    _assert_only_bg_to_gray(fixed, off)


def test_enabled_items_are_unchanged(app):
    ref, rect = _render(app, QStyleFactory.create("Fusion"), with_enabled=True)
    new, rect2 = _render(app, SolidDisabledMenuStyle(QStyleFactory.create("Fusion")), with_enabled=True)
    assert ref.size() == new.size() and rect == rect2
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            assert ref.pixel(x, y) == new.pixel(x, y)
