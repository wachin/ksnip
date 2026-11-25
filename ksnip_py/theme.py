from __future__ import annotations

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
    disabled = QColor("#8a8a8a")
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
