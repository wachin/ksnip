from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QButtonGroup, QColorDialog, QGridLayout, QMenu, QToolButton, QWidget, QWidgetAction


class ColorPaletteMenu(QMenu):
    color_selected = pyqtSignal(QColor)

    def __init__(self, *, show_alpha: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._show_alpha = show_alpha
        self._colors: list[QColor] = []
        self._buttons: list[QToolButton] = []
        self._selected = QColor()
        self._host = QWidget(self)
        self._layout = QGridLayout(self._host)
        self._layout.setContentsMargins(5, 5, 5, 5)
        self._layout.setSpacing(0)
        action = QWidgetAction(self)
        action.setDefaultWidget(self._host)
        self.addAction(action)
        self._reset_colors()

    def set_show_alpha(self, enabled: bool) -> None:
        if self._show_alpha == enabled:
            return
        self._show_alpha = enabled
        if not enabled and self._selected.isValid() and self._selected.alpha() < 255:
            self._selected.setAlpha(255)
        self._reset_colors()

    def select_color(self, color: QColor) -> None:
        if not color.isValid():
            return
        self._selected = QColor(color)
        if not any(existing == color for existing in self._colors):
            self._colors.append(QColor(color))
            self._rebuild()
        for button, existing in zip(self._buttons, self._colors):
            button.setChecked(existing == color)

    def _reset_colors(self) -> None:
        self._colors = [
            QColor(Qt.GlobalColor.red),
            QColor(Qt.GlobalColor.green),
            QColor(Qt.GlobalColor.blue),
            QColor(Qt.GlobalColor.yellow),
            QColor(Qt.GlobalColor.magenta),
            QColor(Qt.GlobalColor.cyan),
            QColor(Qt.GlobalColor.white),
            QColor(Qt.GlobalColor.black),
        ]
        if self._show_alpha:
            self._colors.extend(
                [
                    QColor(0, 255, 255, 100),
                    QColor(255, 0, 255, 100),
                    QColor(255, 255, 0, 100),
                    QColor(255, 255, 255, 100),
                ]
            )
        self._rebuild()

    def _rebuild(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._buttons = []
        group = QButtonGroup(self._host)
        group.setExclusive(True)
        for index, color in enumerate(self._colors):
            button = QToolButton(self._host)
            button.setCheckable(True)
            button.setFixedSize(25, 25)
            button.setIcon(self._color_icon(color, QSize(25, 25)))
            button.setIconSize(QSize(23, 23))
            button.setToolTip(color.name(QColor.NameFormat.HexArgb if color.alpha() < 255 else QColor.NameFormat.HexRgb))
            button.clicked.connect(lambda checked=False, value=QColor(color): self._choose(value))
            group.addButton(button)
            self._layout.addWidget(button, index // 4, index % 4)
            self._buttons.append(button)
        custom = QToolButton(self._host)
        custom.setText("…")
        custom.setToolTip(self.tr("Custom color"))
        custom.setFixedSize(25, 25)
        custom.clicked.connect(self._choose_custom)
        index = len(self._colors)
        self._layout.addWidget(custom, index // 4, index % 4)
        self._button_group = group
        if self._selected.isValid():
            self.select_color(self._selected)

    def _choose(self, color: QColor) -> None:
        self.select_color(color)
        self.color_selected.emit(QColor(color))
        self.hide()

    def _choose_custom(self) -> None:
        options = QColorDialog.ColorDialogOption.ShowAlphaChannel if self._show_alpha else QColorDialog.ColorDialogOption(0)
        initial = self._selected if self._selected.isValid() else QColor(Qt.GlobalColor.white)
        color = QColorDialog.getColor(initial, self, self.tr("Select color"), options)
        if color.isValid():
            self._choose(color)

    @staticmethod
    def _color_icon(color: QColor, size: QSize) -> QIcon:
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        half_width = size.width() // 2
        half_height = size.height() // 2
        painter.fillRect(0, 0, size.width(), size.height(), QColor(Qt.GlobalColor.white))
        painter.fillRect(0, 0, half_width, half_height, QColor(Qt.GlobalColor.gray))
        painter.fillRect(half_width, half_height, size.width() - half_width, size.height() - half_height, QColor(Qt.GlobalColor.gray))
        painter.fillRect(0, 0, size.width(), size.height(), color)
        painter.setPen(QColor(Qt.GlobalColor.gray))
        painter.drawRect(0, 0, size.width() - 1, size.height() - 1)
        painter.end()
        return QIcon(pixmap)
