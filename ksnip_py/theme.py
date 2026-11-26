from __future__ import annotations

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import QApplication


THEME_SYSTEM = "system"
THEME_LIGHT = "light"
THEME_DARK = "dark"
THEMES = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)


def normalize_theme(value: object) -> str:
    theme = str(value or THEME_SYSTEM).strip().lower()
    return theme if theme in THEMES else THEME_SYSTEM


def _dark_palette() -> QPalette:
    palette = QPalette()
    window = QColor("#353535")
    base = QColor("#232323")
    alternate = QColor("#2a2a2a")
    text = QColor("#f2f2f2")
    disabled = QColor("#b5b5b5")
    highlight = QColor("#2a82da")
    palette.setColor(QPalette.ColorRole.Window, window)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, base)
    palette.setColor(QPalette.ColorRole.AlternateBase, alternate)
    palette.setColor(QPalette.ColorRole.ToolTipBase, alternate)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, window)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ff6b6b"))
    palette.setColor(QPalette.ColorRole.Link, highlight)
    palette.setColor(QPalette.ColorRole.Highlight, highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled)
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.ToolTipText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


def apply_theme(app: QApplication, theme: object) -> str:
    """Apply the selected theme for the next UI construction.

    "system" keeps the platform theme (qt6ct/Kvantum on Linux, native on other
    platforms). "light" and "dark" use Qt's Fusion style so the choice works
    consistently on Linux, Windows, and macOS. The main window loads its icons
    after this function, so the matching icon variant is selected.
    """

    resolved = normalize_theme(theme)
    if resolved == THEME_SYSTEM:
        return resolved

    app.setStyle("Fusion")
    if resolved == THEME_DARK:
        app.setPalette(_dark_palette())
        QIcon.setThemeName("Papirus-Dark")
    else:
        app.setPalette(app.style().standardPalette())
        QIcon.setThemeName("Papirus")
    return resolved


class ThemeManager(QObject):
    """Central light/dark theme state for the whole application."""

    theme_changed = pyqtSignal(str, str)  # mode, resolved light/dark

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self._app = app
        self._original_style = app.style().objectName()
        self._original_palette = QPalette(app.palette())
        self._original_icon_theme = QIcon.themeName()
        self._mode = THEME_SYSTEM
        self._resolved = self._system_resolved()
        hints = app.styleHints()
        signal = getattr(hints, "colorSchemeChanged", None)
        if signal is not None:
            signal.connect(self._on_system_color_scheme_changed)

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def resolved(self) -> str:
        return self._resolved

    def icon_variant(self) -> str:
        # icons/dark are light-coloured glyphs for a dark background;
        # icons/light are dark glyphs for a light background.
        return "dark" if self._resolved == THEME_DARK else "light"

    def set_mode(self, mode: object, *, emit: bool = True) -> str:
        previous_mode = self._mode
        previous_resolved = self._resolved
        resolved_mode = normalize_theme(mode)
        self._mode = resolved_mode
        if resolved_mode == THEME_SYSTEM:
            self._restore_system_theme()
            self._resolved = self._system_resolved()
        else:
            self._apply_explicit_theme(resolved_mode)
            self._resolved = resolved_mode
        if emit and (previous_mode != self._mode or previous_resolved != self._resolved):
            self.theme_changed.emit(self._mode, self._resolved)
        return self._mode

    def _restore_system_theme(self) -> None:
        if self._original_style:
            self._app.setStyle(self._original_style)
        self._app.setPalette(self._original_palette)
        QIcon.setThemeName(self._original_icon_theme)

    def _apply_explicit_theme(self, resolved: str) -> None:
        self._app.setStyle("Fusion")
        if resolved == THEME_DARK:
            self._app.setPalette(_dark_palette())
            QIcon.setThemeName("Papirus-Dark")
        else:
            self._app.setPalette(self._app.style().standardPalette())
            QIcon.setThemeName("Papirus")

    def _system_resolved(self) -> str:
        hints = self._app.styleHints()
        scheme = hints.colorScheme() if hasattr(hints, "colorScheme") else None
        if scheme == Qt.ColorScheme.Dark:
            return THEME_DARK
        if scheme == Qt.ColorScheme.Light:
            return THEME_LIGHT
        window = self._app.palette().color(QPalette.ColorRole.Window)
        return THEME_DARK if window.lightness() < 128 else THEME_LIGHT

    def _on_system_color_scheme_changed(self, *_args) -> None:
        if self._mode != THEME_SYSTEM:
            return
        resolved = self._system_resolved()
        if resolved != self._resolved:
            self._resolved = resolved
            self.theme_changed.emit(self._mode, self._resolved)


_theme_manager: ThemeManager | None = None


def init_theme_manager(app: QApplication) -> ThemeManager:
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager(app)
    return _theme_manager


def theme_manager() -> ThemeManager | None:
    return _theme_manager
