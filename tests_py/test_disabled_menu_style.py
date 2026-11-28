"""Version-independent check: disabled menu items are drawn in solid #5c5c5c.

Run with:  QT_QPA_PLATFORM=offscreen python -m pytest tests_py/test_disabled_menu_style.py
"""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import QApplication, QMenu, QProxyStyle, QStyle, QStyleFactory, QStyleOptionMenuItem

from ksnip_py.menu_style import (
    SolidDisabledMenuStyle,
    SolidMenu,
    enabled_shortcut_color,
)

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


class _FloodBackgroundStyle(QProxyStyle):
    """Base style that fills the whole item, defeating the alpha-buffer path."""

    def drawControl(self, element, option, painter, widget=None):  # noqa: N802
        if (
            element == QStyle.ControlElement.CE_MenuItem
            and isinstance(option, QStyleOptionMenuItem)
        ):
            painter.fillRect(option.rect, QColor("#1e1e1e"))
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


def _shortcut_menu(app, menu_class, style):
    """Render one enabled item with a shortcut and return its image and rect."""

    app.setStyle(style)
    _dark(app)
    menu = menu_class()
    action = QAction("Open", menu)
    action.setShortcut(QKeySequence("Ctrl+Shift+S"))
    menu.addAction(action)
    menu.ensurePolished()
    menu.resize(menu.sizeHint())
    menu.show()
    app.processEvents()
    image = menu.grab().toImage()
    rect = menu.actionGeometry(action)
    menu.close()
    return image, rect


def _text_pixels(image, rect):
    count = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            if QColor(image.pixel(x, y)).lightness() > 128:
                count += 1
    return count


def test_shortcut_repaint_only_happens_for_the_wrapped_style(app):
    """The repaint is what avoids a duplicate label under the native style."""

    assert enabled_shortcut_color(QStyleFactory.create("Fusion")) is None
    assert enabled_shortcut_color(SolidDisabledMenuStyle(QStyleFactory.create("Fusion"))) is None
    colored = SolidDisabledMenuStyle(
        QStyleFactory.create("Fusion"), enabled_color=QColor("#111214")
    )
    color = enabled_shortcut_color(colored)
    assert color is not None and color.name() == "#111214"


@pytest.mark.parametrize("name", [n for n in ("Windows", "Fusion") if n in QStyleFactory.keys()])
def test_native_style_draws_the_shortcut_once(app, name):
    """SolidMenu must not add a second label when the style paints it already."""

    plain, rect_plain = _shortcut_menu(app, QMenu, QStyleFactory.create(name))
    solid, rect_solid = _shortcut_menu(app, SolidMenu, QStyleFactory.create(name))
    assert plain.size() == solid.size() and rect_plain == rect_solid
    assert _text_pixels(plain, rect_plain) == _text_pixels(solid, rect_solid)


def test_wrapped_style_still_paints_the_shortcut(app):
    """The enabled-color path relies on SolidMenu drawing the label it stripped."""

    plain, rect_plain = _shortcut_menu(
        app, QMenu, SolidDisabledMenuStyle(QStyleFactory.create("Fusion"), enabled_color=QColor("#f2f2f2"))
    )
    solid, rect_solid = _shortcut_menu(
        app, SolidMenu, SolidDisabledMenuStyle(QStyleFactory.create("Fusion"), enabled_color=QColor("#f2f2f2"))
    )
    assert _text_pixels(plain, rect_plain) < _text_pixels(solid, rect_solid)


def test_style_fallback_does_not_duplicate_the_shortcut(app):
    """When the buffer cannot be recoloured the base style keeps the label."""

    style = SolidDisabledMenuStyle(
        _FloodBackgroundStyle(QStyleFactory.create("Fusion")),
        enabled_color=QColor("#f2f2f2"),
    )
    plain, rect_plain = _shortcut_menu(app, QMenu, SolidDisabledMenuStyle(
        _FloodBackgroundStyle(QStyleFactory.create("Fusion")),
        enabled_color=QColor("#f2f2f2"),
    ))
    solid, rect_solid = _shortcut_menu(app, SolidMenu, style)
    assert _text_pixels(plain, rect_plain) == _text_pixels(solid, rect_solid)


def test_enabled_items_with_an_icon_keep_the_icon_colours(app, tmp_path):
    """Tinting the whole item used to flatten the icon into a silhouette."""

    icon_path = tmp_path / "teal.svg"
    icon_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
        '<rect x="2" y="2" width="20" height="20" rx="5" fill="#0f766e"/></svg>',
        encoding="utf-8",
    )
    app.setStyle(
        SolidDisabledMenuStyle(
            QStyleFactory.create("Fusion"), enabled_color=QColor("#111214")
        )
    )
    _dark(app)
    menu = QMenu()
    action = QAction(QIcon(str(icon_path)), "Open", menu)
    action.setShortcut(QKeySequence("Ctrl+O"))
    menu.addAction(action)
    menu.ensurePolished()
    menu.resize(menu.sizeHint())
    menu.show()
    app.processEvents()

    image = menu.grab().toImage()
    rect = menu.actionGeometry(action)
    teal = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            colour = QColor(image.pixel(x, y))
            if (
                abs(colour.red() - 0x0F) < 26
                and abs(colour.green() - 0x76) < 26
                and abs(colour.blue() - 0x6E) < 26
            ):
                teal += 1
    menu.close()
    assert teal > 10, "the menu icon was flattened by the enabled item tint"
