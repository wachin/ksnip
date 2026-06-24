from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QContextMenuEvent, QEnterEvent, QKeyEvent, QMouseEvent, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QMenu, QVBoxLayout, QWidget


class PinWindow(QWidget):
    close_other_requested = pyqtSignal(object)
    close_all_requested = pyqtSignal()

    def __init__(self, pixmap: QPixmap, title: str) -> None:
        super().__init__(None)
        self._margin = 10
        self._min_size = 50
        self._image = QPixmap(pixmap)
        self._is_moving = False
        self._move_offset = QPoint()

        self.setWindowTitle(title)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setContentsMargins(self._margin, self._margin, self._margin, self._margin)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(self._margin, self._margin, self._margin, self._margin)

        self._central_widget = QLabel(self)
        self._central_widget.setPixmap(self._image)
        self._layout.addWidget(self._central_widget)

        self._drop_shadow_effect = QGraphicsDropShadowEffect(self)
        self._drop_shadow_effect.setColor(QColor(160, 160, 160))
        self._drop_shadow_effect.setBlurRadius(self._margin * 2)
        self._drop_shadow_effect.setOffset(0)
        self.setGraphicsEffect(self._drop_shadow_effect)
        self.adjustSize()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self.close()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_moving = True
            self._move_offset = event.globalPosition().toPoint() - self.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_moving = False
            self._move_offset = QPoint()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._is_moving:
            self.move(event.globalPosition().toPoint() - self._move_offset)
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802
        menu = QMenu(self)
        menu.addAction("Close", self.close)
        menu.addAction("Close Other", lambda: self.close_other_requested.emit(self))
        menu.addAction("Close All", self.close_all_requested.emit)
        menu.exec(event.globalPos())

    def enterEvent(self, event: QEnterEvent) -> None:  # noqa: N802
        self._drop_shadow_effect.setBlurRadius(self._margin * 2 + 4)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._drop_shadow_effect.setBlurRadius(self._margin * 2)
        super().leaveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        delta = event.pixelDelta().y()
        if delta == 0:
            delta = event.angleDelta().y() // 4
        scaled_width = self._central_widget.width() + delta // 10
        scaled_height = self._central_widget.height() + delta // 10
        if scaled_width <= self._min_size or scaled_height <= self._min_size:
            return
        scaled_image = self._image.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._central_widget.setPixmap(scaled_image)
        self.adjustSize()
        super().wheelEvent(event)
