"""Solid-gray rendering of disabled QMenu items, independent of the base style.

How a *disabled* menu item is drawn is decided by the active QStyle (Fusion,
Windows, Kvantum, qt6ct's style, ...), not by the application.  Some styles
paint disabled text "etched" (a light copy offset by 1 px under the gray text),
dither it, or ignore ``QPalette.Disabled`` for menus.  Palette entries, QSS and
``QIcon.Mode.Disabled`` pixmaps cannot stop that.

``SolidDisabledMenuStyle`` wraps whatever style is active.  For a disabled
``CE_MenuItem`` it lets the *base style* lay out and draw the item as if it
were enabled (so icon, text, shortcut, arrow and check indicator are in exactly
the same place as for enabled items), but into a transparent buffer with every
background brush cleared.  The buffer's alpha channel is then the exact shape of
everything the item draws; that shape is filled with one solid colour and
blitted.  Result: text, shortcut, arrow, check mark and icon are all #5c5c5c,
with no etching, dithering or opacity, whatever the base style does.

Enabled items, separators, scrollers, tear-offs, menu bars, toolbars and every
other control are delegated untouched to the base style.
"""

from __future__ import annotations

from math import ceil

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPalette
from PyQt6.QtWidgets import QProxyStyle, QStyle, QStyleFactory, QStyleOptionMenuItem

DISABLED_MENU_COLOR = QColor("#5c5c5c")

_ITEM_TYPES = (
    QStyleOptionMenuItem.MenuItemType.Normal,
    QStyleOptionMenuItem.MenuItemType.DefaultItem,
    QStyleOptionMenuItem.MenuItemType.SubMenu,
)
# If the base style fills (almost) the whole item rect even with cleared
# brushes, recolouring the alpha would paint a gray slab; fall back instead.
_MAX_COVERAGE = 0.55


class SolidDisabledMenuStyle(QProxyStyle):
    def __init__(self, base: QStyle | None = None, color: QColor = DISABLED_MENU_COLOR) -> None:
        super().__init__(base)
        self._color = QColor(color)

    def drawControl(self, element, option, painter, widget=None):  # noqa: N802
        if (
            element == QStyle.ControlElement.CE_MenuItem
            and isinstance(option, QStyleOptionMenuItem)
            and option.menuItemType in _ITEM_TYPES
            and not (option.state & QStyle.StateFlag.State_Enabled)
            and option.rect.width() > 0
            and option.rect.height() > 0
            and self._draw_disabled_item(option, painter, widget)
        ):
            return
        super().drawControl(element, option, painter, widget)

    def _draw_disabled_item(self, option, painter, widget) -> bool:
        rect: QRect = option.rect
        dpr = max(1.0, painter.device().devicePixelRatioF())
        image = QImage(
            ceil(rect.width() * dpr),
            ceil(rect.height() * dpr),
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.setDevicePixelRatio(dpr)
        image.fill(Qt.GlobalColor.transparent)

        item = QStyleOptionMenuItem(option)
        # Draw as a plain *enabled*, un-highlighted item: no disabled branch of
        # the base style (etch, dither, palette quirks) can run.
        item.state = (item.state | QStyle.StateFlag.State_Enabled) & ~(
            QStyle.StateFlag.State_Selected
            | QStyle.StateFlag.State_Sunken
            | QStyle.StateFlag.State_MouseOver
        )
        palette = QPalette(item.palette)
        clear = QBrush(QColor(0, 0, 0, 0))
        for role in (
            QPalette.ColorRole.Window,
            QPalette.ColorRole.Button,
            QPalette.ColorRole.Base,
            QPalette.ColorRole.AlternateBase,
        ):
            palette.setBrush(role, clear)
        opaque = QColor(0, 0, 0)  # colour is irrelevant, alpha must be 1
        for role in (
            QPalette.ColorRole.WindowText,
            QPalette.ColorRole.Text,
            QPalette.ColorRole.ButtonText,
        ):
            palette.setColor(role, opaque)
        item.palette = palette

        buffer = QPainter(image)
        buffer.setRenderHints(painter.renderHints())
        buffer.translate(-rect.topLeft())
        super().drawControl(QStyle.ControlElement.CE_MenuItem, item, buffer, widget)
        buffer.end()

        if self._coverage(image) > _MAX_COVERAGE:
            return False

        tint = QPainter(image)
        tint.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        tint.fillRect(QRectF(0, 0, rect.width(), rect.height()), self._color)
        tint.end()
        painter.drawImage(rect.topLeft(), image)
        return True

    @staticmethod
    def _coverage(image: QImage) -> float:
        alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
        pointer = alpha.constBits()
        if pointer is None:
            return 0.0
        pointer.setsize(alpha.sizeInBytes())
        data = bytes(pointer)
        return 0.0 if not data else sum(1 for b in data if b > 128) / len(data)


def create_menu_safe_style(name: str | None) -> QStyle:
    """Return the named style wrapped in :class:`SolidDisabledMenuStyle`."""
    base = QStyleFactory.create(name) if name else None
    if base is None:
        base = QStyleFactory.create("Fusion")
    return SolidDisabledMenuStyle(base)
