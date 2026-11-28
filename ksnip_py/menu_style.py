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

Enabled items are delegated untouched *unless* an enabled colour is configured,
which the light and dark themes do. In that case the same buffer-and-tint pass
runs for them, the shortcut label is removed from the buffered item, and
``SolidMenu`` draws it once in the enabled colour. Under the native style (the
"system" theme) that pass does not run: the base style draws the label itself,
so ``SolidMenu`` must not add a second copy.

Separators, scrollers, tear-offs, menu bars, toolbars and every other control
are delegated untouched to the base style.
"""

from __future__ import annotations

from math import ceil

from PyQt6.QtCore import QRect, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QKeySequence, QPainter, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QMenu,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QStyleOptionMenuItem,
)

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
    def __init__(
        self,
        base: QStyle | None = None,
        color: QColor = DISABLED_MENU_COLOR,
        enabled_color: QColor | None = None,
    ) -> None:
        super().__init__(base)
        self._color = QColor(color)
        self._enabled_color = (
            QColor(enabled_color) if enabled_color is not None else None
        )
        # Items whose enabled shortcut this style left in the base style's hands
        # because the alpha buffer could not be recoloured.
        self._native_shortcut_rects: set[tuple[int, int, int, int]] = set()

    @property
    def enabled_color(self) -> QColor | None:
        """Colour :class:`SolidMenu` must repaint enabled shortcuts with."""

        if self._enabled_color is None:
            return None
        return QColor(self._enabled_color)

    def begin_menu_paint(self) -> None:
        """Forget the previous paint pass, before the menu draws its items."""

        self._native_shortcut_rects.clear()

    def drew_native_shortcut(self, rect: QRect) -> bool:
        """Whether the base style already drew this item's shortcut itself."""

        return (
            rect.x(),
            rect.y(),
            rect.width(),
            rect.height(),
        ) in self._native_shortcut_rects

    def drawControl(self, element, option, painter, widget=None):  # noqa: N802
        if (
            element == QStyle.ControlElement.CE_MenuItem
            and isinstance(option, QStyleOptionMenuItem)
            and option.menuItemType in _ITEM_TYPES
            and not (option.state & QStyle.StateFlag.State_Selected)
            and not (option.state & QStyle.StateFlag.State_MouseOver)
            and option.rect.width() > 0
            and option.rect.height() > 0
        ):
            enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
            color = self._enabled_color if enabled else self._color
            if color is not None and enabled and not option.icon.isNull():
                # Tinting flattens the whole item, icon included. Let the base
                # style draw enabled items that carry an icon, so the icon keeps
                # its colours; the base style also draws their shortcut, which
                # SolidMenu must not repeat.
                if "\t" in option.text:
                    rect = option.rect
                    self._native_shortcut_rects.add(
                        (rect.x(), rect.y(), rect.width(), rect.height())
                    )
                super().drawControl(element, option, painter, widget)
                return
            if color is not None and self._draw_solid_item(
                option, painter, widget, color
            ):
                return
            # The base style keeps the shortcut in its own hands here; tell
            # SolidMenu not to paint a second copy.
            if color is not None and enabled and "\t" in option.text:
                rect = option.rect
                self._native_shortcut_rects.add(
                    (rect.x(), rect.y(), rect.width(), rect.height())
                )
        super().drawControl(element, option, painter, widget)

    def _draw_solid_item(
        self,
        option: QStyleOptionMenuItem,
        painter,
        widget,
        color: QColor,
    ) -> bool:
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
        # Strip the shortcut from the buffered item. Qt draws the shortcut
        # again after CE_MenuItem; SolidMenu repaints that copy in the enabled
        # color. Keeping it here would leave a duplicate gray copy behind.
        if option.state & QStyle.StateFlag.State_Enabled and "\t" in item.text:
            item.text = item.text.split("\t", 1)[0]
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
        tint.fillRect(QRectF(0, 0, rect.width(), rect.height()), color)
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


def enabled_shortcut_color(style: QStyle) -> QColor | None:
    """Return the colour :class:`SolidMenu` must repaint shortcuts with.

    Only :class:`SolidDisabledMenuStyle` removes the enabled shortcut from the
    buffered item, so only that case needs a repaint.  Any other style (the
    native platform style used by the "system" theme, for example) draws the
    shortcut itself from the tabbed item text; repainting it again would leave
    two labels on top of each other.
    """

    if not isinstance(style, SolidDisabledMenuStyle):
        return None
    return style.enabled_color


class SolidMenu(QMenu):
    """QMenu that paints enabled shortcut labels in the enabled text color.

    Qt draws enabled shortcut labels with a separate, lighter color. The
    disabled-menu style removes that shortcut from its buffered item; this
    subclass draws it once in the enabled color. Disabled shortcuts stay in
    the buffered item and keep the theme's disabled gray.

    The repaint only happens when :class:`SolidDisabledMenuStyle` is active with
    an enabled color, because that is the only situation where the shortcut was
    removed from the item. Under the native style ("system" theme on Windows)
    the style already draws it, and a second pass duplicates the label.
    """

    def paintEvent(self, event):  # noqa: N802
        style = self.style()
        if isinstance(style, SolidDisabledMenuStyle):
            style.begin_menu_paint()
        super().paintEvent(event)

        color = enabled_shortcut_color(style)
        if color is None:
            return
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(color)
        metrics = painter.fontMetrics()
        active = self.activeAction()
        for action in self.actions():
            if (
                not action.isEnabled()
                or not action.isVisible()
                or action.isSeparator()
                or action.menu() is not None
                or action == active
            ):
                continue
            shortcut = action.shortcut().toString(
                QKeySequence.SequenceFormat.NativeText
            )
            if not shortcut:
                continue
            rect = self.actionGeometry(action)
            if rect.isNull() or (
                isinstance(style, SolidDisabledMenuStyle)
                and style.drew_native_shortcut(rect)
            ):
                continue
            width = metrics.horizontalAdvance(shortcut)
            x = self.width() - 10 - width
            painter.drawText(
                QRect(x, rect.y(), width, rect.height()),
                int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                shortcut,
            )
        painter.end()

    def addMenu(self, *args):  # noqa: N802
        if len(args) == 1 and isinstance(args[0], str):
            icon, title = None, args[0]
        elif len(args) == 2:
            icon, title = args
        else:
            return super().addMenu(*args)
        menu = SolidMenu(self)
        menu.setTitle(title)
        if icon is not None:
            menu.setIcon(icon)
        self.addAction(menu.menuAction())
        return menu


def create_menu_safe_style(
    name: str | None,
    color: QColor = DISABLED_MENU_COLOR,
    enabled_color: QColor | None = None,
) -> QStyle:
    """Return the named style wrapped in :class:`SolidDisabledMenuStyle`."""
    base = QStyleFactory.create(name) if name else None
    if base is None:
        base = QStyleFactory.create("Fusion")
    return SolidDisabledMenuStyle(base, color, enabled_color)
