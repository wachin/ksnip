from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import Enum
from math import hypot
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QContextMenuEvent, QFont, QFontMetrics, QIcon, QImage, QKeySequence, QMouseEvent, QPainter, QPalette, QPen, QPixmap, QPolygon, QTransform
from PyQt6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QMenu, QSizePolicy, QVBoxLayout

from .spellcheck import SpellCheckTextEdit, load_spellcheck_scheme


class TextInputDialog(QDialog):
    def __init__(self, parent=None, *, title: str, text: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        hint = QLabel("Shift+Enter adds a new line. Ctrl+Enter accepts.", self)
        layout.addWidget(hint)

        self.editor = SpellCheckTextEdit(self)
        self.editor.set_spellcheck_color_scheme(load_spellcheck_scheme())
        self.editor.setPlainText(text)
        layout.addWidget(self.editor, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.accept()
            return
        super().keyPressEvent(event)

    def text(self) -> str:
        return self.editor.toPlainText()


class InlineTextEditor(SpellCheckTextEdit):
    accepted = pyqtSignal()
    canceled = pyqtSignal()
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._finished = False

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo_requested.emit()
            return
        if event.matches(QKeySequence.StandardKey.Redo):
            self.redo_requested.emit()
            return
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter} and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._emit_accepted()
            return
        if event.key() == Qt.Key.Key_Escape:
            self._emit_canceled()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        if event.reason() == Qt.FocusReason.PopupFocusReason or QApplication.activePopupWidget() is not None:
            super().focusOutEvent(event)
            return
        self._emit_accepted()
        super().focusOutEvent(event)

    def _emit_accepted(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.accepted.emit()

    def _emit_canceled(self) -> None:
        if self._finished:
            return
        self._finished = True
        self.canceled.emit()


class Tool(str, Enum):
    SELECT = "select"
    IMAGE = "image"
    STICKER = "sticker"
    PEN = "pen"
    MARKER_PEN = "marker_pen"
    LINE = "line"
    ARROW = "arrow"
    DOUBLE_ARROW = "double_arrow"
    RECT = "rect"
    ELLIPSE = "ellipse"
    MARKER_RECT = "marker_rect"
    MARKER_ELLIPSE = "marker_ellipse"
    TEXT = "text"
    TEXT_POINTER = "text_pointer"
    TEXT_ARROW = "text_arrow"
    NUMBER = "number"
    NUMBER_POINTER = "number_pointer"
    NUMBER_ARROW = "number_arrow"
    BLUR = "blur"
    PIXELATE = "pixelate"
    CROP = "crop"


class FillMode(str, Enum):
    BORDER_AND_NO_FILL = "border_and_no_fill"
    BORDER_AND_FILL = "border_and_fill"
    NO_BORDER_AND_NO_FILL = "no_border_and_no_fill"
    NO_BORDER_AND_FILL = "no_border_and_fill"


@dataclass
class CanvasState:
    path: str | None = None
    dirty: bool = False


@dataclass
class OverlayItem:
    kind: Tool
    start: QPoint
    end: QPoint
    color: QColor
    pen_width: int
    text: str | None = None
    font_family: str | None = None
    font_point_size: int | None = None
    fill_color: QColor | None = None
    opacity: float = 1.0
    fill_mode: FillMode = FillMode.BORDER_AND_FILL
    bold: bool = False
    italic: bool = False
    underline: bool = False
    text_color: QColor | None = None
    shadow: bool = False
    scaling: float = 1.0
    sticker_path: str | None = None
    image: QImage | None = None

    def clone(self) -> "OverlayItem":
        return OverlayItem(
            kind=self.kind,
            start=QPoint(self.start),
            end=QPoint(self.end),
            color=QColor(self.color),
            pen_width=self.pen_width,
            text=self.text,
            font_family=self.font_family,
            font_point_size=self.font_point_size,
            fill_color=QColor(self.fill_color) if self.fill_color is not None else None,
            opacity=self.opacity,
            fill_mode=self.fill_mode,
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            text_color=QColor(self.text_color) if self.text_color is not None else None,
            shadow=self.shadow,
            scaling=self.scaling,
            sticker_path=self.sticker_path,
            image=self.image.copy() if self.image is not None else None,
        )

    def move_by(self, delta: QPoint) -> None:
        self.start += delta
        self.end += delta

    def bounds(self) -> QRect:
        if self.kind == Tool.TEXT:
            if self.start != self.end:
                return QRect(self.start, self.end).normalized()
            lines = (self.text or "").splitlines() or [""]
            font = QFont()
            if self.font_family:
                font.setFamily(self.font_family)
            font.setPointSize(self.font_point_size or max(10, self.pen_width * 4))
            font.setBold(self.bold)
            font.setItalic(self.italic)
            font.setUnderline(self.underline)
            metrics = QFontMetrics(font)
            width = max(60, max(metrics.horizontalAdvance(line or " ") for line in lines) + 18)
            line_height = max(18, metrics.lineSpacing())
            height = max(28, line_height * len(lines) + 10)
            return QRect(self.start.x(), self.start.y(), width, height)
        if self.kind == Tool.TEXT_ARROW:
            lines = (self.text or "").splitlines() or [""]
            width = max(96, max(len(line) for line in lines) * 10 + 24)
            height = max(34, ((self.font_point_size or 14) + 8) * len(lines) + 10)
            label = QRect(self.start.x() + 8, self.start.y() - height // 2, width, height)
            return QRect(self.start, self.end).normalized().united(label).adjusted(-6, -6, 6, 6)
        if self.kind == Tool.NUMBER_ARROW:
            radius = max(14, self.font_point_size or 14)
            bubble = QRect(self.start.x() - radius, self.start.y() - radius, radius * 2, radius * 2)
            return QRect(self.start, self.end).normalized().united(bubble).adjusted(-6, -6, 6, 6)
        if self.kind == Tool.IMAGE and self.image is not None:
            return QRect(self.start, self.end).normalized()
        return QRect(self.start, self.end).normalized().adjusted(-6, -6, 6, 6)


@dataclass
class CanvasSnapshot:
    image: QImage
    items: list[OverlayItem]


class AnnotationCanvas(QLabel):
    changed = pyqtSignal()
    zoom_changed = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self.setMinimumSize(640, 360)

        self._tool = Tool.SELECT
        self._color = QColor("#df5a17")
        self._pen_width = 3
        self._font_family = QFont().family()
        self._font_point_size = 14
        self._fill_color = QColor(246, 189, 96, 80)
        self._text_color = QColor("#ffffff")
        self._opacity = 1.0
        self._fill_mode = FillMode.BORDER_AND_FILL
        self._bold = False
        self._italic = False
        self._underline = False
        self._shadow = True
        self._scaling = 1.0
        self._number_seed = 1
        self._sticker_path: str | None = None
        self._available_sticker_paths: list[str] = []
        self._image = QImage()
        self._items: list[OverlayItem] = []
        self._preview_start: QPoint | None = None
        self._preview_end: QPoint | None = None
        self._last_point: QPoint | None = None
        self._selected_item_indices: list[int] = []
        self._primary_selected_item_index: int | None = None
        self._drag_start: QPoint | None = None
        self._active_handle: str | None = None
        self._undo_stack: list[CanvasSnapshot] = []
        self._redo_stack: list[CanvasSnapshot] = []
        self._zoom_percent = 100
        self._inline_text_editor: InlineTextEditor | None = None
        self._editing_text_index: int | None = None
        self._editing_text_original: str | None = None
        self._editing_text_is_new = False
        self.state = CanvasState()

    @staticmethod
    def _is_line_like(tool: Tool) -> bool:
        return tool in (Tool.LINE, Tool.ARROW, Tool.DOUBLE_ARROW, Tool.TEXT_ARROW, Tool.NUMBER_ARROW)

    @staticmethod
    def _is_shape_like(tool: Tool) -> bool:
        return tool in (Tool.RECT, Tool.ELLIPSE, Tool.MARKER_RECT, Tool.MARKER_ELLIPSE)

    @staticmethod
    def _is_text_like(tool: Tool) -> bool:
        return tool in (Tool.TEXT, Tool.TEXT_POINTER, Tool.TEXT_ARROW)

    @staticmethod
    def _is_number_like(tool: Tool) -> bool:
        return tool in (Tool.NUMBER, Tool.NUMBER_POINTER, Tool.NUMBER_ARROW)

    @staticmethod
    def _has_fill(fill_mode: FillMode) -> bool:
        return fill_mode in {FillMode.BORDER_AND_FILL, FillMode.NO_BORDER_AND_FILL}

    @staticmethod
    def _has_border(fill_mode: FillMode) -> bool:
        return fill_mode in {FillMode.BORDER_AND_FILL, FillMode.BORDER_AND_NO_FILL}

    def has_image(self) -> bool:
        return not self._image.isNull()

    def image(self) -> QImage:
        return self._compose_image()

    def add_image_item(self, image: QImage, position: QPoint | None = None) -> bool:
        if self._image.isNull() or image.isNull():
            return False
        self._push_undo_state()
        top_left = QPoint(position) if position is not None else QPoint(0, 0)
        bottom_right = QPoint(top_left.x() + image.width(), top_left.y() + image.height())
        self._items.append(
            OverlayItem(
                kind=Tool.IMAGE,
                start=top_left,
                end=bottom_right,
                color=QColor(self._color),
                pen_width=1,
                opacity=1.0,
                shadow=self._shadow,
                scaling=1.0,
                image=image.copy(),
            )
        )
        self._select_single_item(len(self._items) - 1)
        self._mark_dirty()
        self._refresh()
        return True

    @staticmethod
    def _serialize_item(item: OverlayItem) -> dict:
        image_payload = None
        if item.image is not None and not item.image.isNull():
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            item.image.save(buffer, "PNG")
            image_payload = base64.b64encode(bytes(byte_array)).decode("ascii")
        return {
            "kind": item.kind.value,
            "start": [item.start.x(), item.start.y()],
            "end": [item.end.x(), item.end.y()],
            "color": item.color.name(QColor.NameFormat.HexArgb),
            "pen_width": item.pen_width,
            "text": item.text,
            "font_family": item.font_family,
            "font_point_size": item.font_point_size,
            "fill_color": item.fill_color.name(QColor.NameFormat.HexArgb) if item.fill_color is not None else None,
            "opacity": item.opacity,
            "fill_mode": item.fill_mode.value,
            "bold": item.bold,
            "italic": item.italic,
            "underline": item.underline,
            "text_color": item.text_color.name(QColor.NameFormat.HexArgb) if item.text_color is not None else None,
            "shadow": item.shadow,
            "scaling": item.scaling,
            "sticker_path": item.sticker_path,
            "image_png_base64": image_payload,
        }

    @staticmethod
    def _deserialize_item(payload: dict) -> OverlayItem:
        image = None
        if payload.get("image_png_base64"):
            raw = base64.b64decode(payload["image_png_base64"])
            image = QImage()
            image.loadFromData(raw, "PNG")
        return OverlayItem(
            kind=Tool(payload["kind"]),
            start=QPoint(payload["start"][0], payload["start"][1]),
            end=QPoint(payload["end"][0], payload["end"][1]),
            color=QColor(payload["color"]),
            pen_width=payload["pen_width"],
            text=payload.get("text"),
            font_family=payload.get("font_family"),
            font_point_size=payload.get("font_point_size"),
            fill_color=QColor(payload["fill_color"]) if payload.get("fill_color") else None,
            opacity=payload.get("opacity", 1.0),
            fill_mode=FillMode(payload.get("fill_mode", FillMode.BORDER_AND_FILL.value)),
            bold=payload.get("bold", False),
            italic=payload.get("italic", False),
            underline=payload.get("underline", False),
            text_color=QColor(payload["text_color"]) if payload.get("text_color") else None,
            shadow=payload.get("shadow", False),
            scaling=payload.get("scaling", 1.0),
            sticker_path=payload.get("sticker_path"),
            image=image,
        )

    def set_image(self, image: QImage, path: str | None = None) -> None:
        self._image = image.copy()
        self._items = []
        self._undo_stack = []
        self._redo_stack = []
        self._clear_selection()
        self._drag_start = None
        self._active_handle = None
        self.state = CanvasState(path=path, dirty=False)
        self._preview_start = None
        self._preview_end = None
        self._last_point = None
        self._refresh()

    def selected_item_count(self) -> int:
        self._normalize_selection()
        return len(self._selected_item_indices)

    def has_single_selected_item(self) -> bool:
        return self.selected_item_count() == 1

    def _normalize_selection(self) -> None:
        valid_indices = [index for index in self._selected_item_indices if 0 <= index < len(self._items)]
        if valid_indices != self._selected_item_indices:
            self._selected_item_indices = valid_indices
        if self._primary_selected_item_index not in self._selected_item_indices:
            self._primary_selected_item_index = self._selected_item_indices[-1] if self._selected_item_indices else None

    def _clear_selection(self) -> None:
        self._selected_item_indices = []
        self._primary_selected_item_index = None

    def _select_single_item(self, index: int | None) -> None:
        if index is None:
            self._clear_selection()
            return
        self._selected_item_indices = [index]
        self._primary_selected_item_index = index

    def _toggle_item_selection(self, index: int) -> None:
        if index in self._selected_item_indices:
            self._selected_item_indices = [item_index for item_index in self._selected_item_indices if item_index != index]
            if self._primary_selected_item_index == index:
                self._primary_selected_item_index = self._selected_item_indices[-1] if self._selected_item_indices else None
            return
        self._selected_item_indices.append(index)
        self._primary_selected_item_index = index

    def _primary_selected_index(self) -> int | None:
        self._normalize_selection()
        return self._primary_selected_item_index

    def _primary_selected_item(self) -> OverlayItem | None:
        index = self._primary_selected_index()
        return self._items[index] if index is not None else None

    def set_tool(self, tool: Tool) -> None:
        self._tool = tool

    def tool(self) -> Tool:
        return self._tool

    def set_color(self, color: QColor) -> None:
        self._color = QColor(color)

    def set_pen_width(self, width: int) -> None:
        self._pen_width = max(1, width)

    def set_font_family(self, family: str) -> None:
        self._font_family = family

    def set_font_point_size(self, point_size: int) -> None:
        self._font_point_size = max(1, point_size)

    def set_fill_color(self, color: QColor) -> None:
        self._fill_color = QColor(color)

    def set_text_color(self, color: QColor) -> None:
        self._text_color = QColor(color)

    def text_color(self) -> QColor:
        return QColor(self._text_color)

    def set_opacity(self, opacity: float) -> None:
        self._opacity = max(0.0, min(1.0, opacity))

    def set_fill_mode(self, fill_mode: FillMode) -> None:
        self._fill_mode = fill_mode

    def set_bold(self, bold: bool) -> None:
        self._bold = bool(bold)

    def set_italic(self, italic: bool) -> None:
        self._italic = bool(italic)

    def set_underline(self, underline: bool) -> None:
        self._underline = bool(underline)

    def set_shadow(self, shadow: bool) -> None:
        self._shadow = bool(shadow)

    def set_scaling(self, scaling: float) -> None:
        self._scaling = max(0.0, scaling)

    def set_number_seed(self, value: int) -> None:
        self._number_seed = max(1, int(value))

    def number_seed(self) -> int:
        return self._number_seed

    def set_sticker_paths(self, paths: list[str]) -> None:
        self._available_sticker_paths = [path for path in paths if Path(path).exists()]
        if self._sticker_path not in self._available_sticker_paths:
            self._sticker_path = self._available_sticker_paths[0] if self._available_sticker_paths else None

    def set_sticker_path(self, path: str | None) -> None:
        self._sticker_path = path if path and Path(path).exists() else None

    def sticker_path(self) -> str | None:
        return self._sticker_path

    def zoom_percent(self) -> int:
        return self._zoom_percent

    def set_zoom_percent(self, percent: int) -> None:
        resolved = max(10, min(800, int(percent)))
        if resolved == self._zoom_percent:
            return
        self._zoom_percent = resolved
        self.zoom_changed.emit(self._zoom_percent)
        self._refresh()

    def zoom_in(self) -> None:
        self.set_zoom_percent(self._zoom_percent + 10)

    def zoom_out(self) -> None:
        self.set_zoom_percent(self._zoom_percent - 10)

    def reset_zoom(self) -> None:
        self.set_zoom_percent(100)

    def fit_to_size(self, available_size: QSize) -> None:
        if self._image.isNull() or available_size.width() <= 0 or available_size.height() <= 0:
            return
        width_ratio = available_size.width() / self._image.width()
        height_ratio = available_size.height() / self._image.height()
        factor = min(width_ratio, height_ratio)
        self.set_zoom_percent(max(10, min(800, round(factor * 100))))

    def selected_item_color(self) -> QColor | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return QColor(item.color)

    def selected_item_pen_width(self) -> int | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return item.pen_width

    def selected_item_font_family(self) -> str | None:
        item = self._primary_selected_item()
        if item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return None
        return item.font_family or self._font_family

    def selected_item_font_point_size(self) -> int | None:
        item = self._primary_selected_item()
        if item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return None
        return item.font_point_size or self._font_point_size

    def selected_item_fill_color(self) -> QColor | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return QColor(item.fill_color) if item.fill_color is not None else None

    def selected_item_text_color(self) -> QColor | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return QColor(item.text_color) if item.text_color is not None else None

    def selected_item_opacity(self) -> int | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return round(item.opacity * 100)

    def selected_item_fill_mode(self) -> FillMode | None:
        item = self._primary_selected_item()
        if item is None or item.kind not in (Tool.RECT, Tool.ELLIPSE, Tool.TEXT, Tool.TEXT_ARROW, Tool.NUMBER, Tool.NUMBER_ARROW):
            return None
        return item.fill_mode

    def selected_item_bold(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return None
        return item.bold

    def selected_item_italic(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return None
        return item.italic

    def selected_item_underline(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return None
        return item.underline

    def selected_item_shadow(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return item.shadow

    def selected_item_scaling(self) -> int | None:
        item = self._primary_selected_item()
        if item is None or item.kind not in (Tool.IMAGE, Tool.STICKER):
            return None
        return round(item.scaling * 100)

    def selected_item_number(self) -> int | None:
        item = self._primary_selected_item()
        if item is None or not self._is_number_like(item.kind) or not item.text or not item.text.isdigit():
            return None
        return int(item.text)

    def selected_item_sticker_path(self) -> str | None:
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.STICKER:
            return None
        return item.sticker_path

    def mark_saved(self, path: str | None) -> None:
        self.state.path = path
        self.state.dirty = False
        self.changed.emit()

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def has_selected_item(self) -> bool:
        return self.selected_item_count() > 0

    def selected_item_kind(self) -> Tool | None:
        if not self.has_single_selected_item():
            return None
        item = self._primary_selected_item()
        return item.kind if item is not None else None

    def undo(self) -> None:
        if self._inline_text_editor is not None:
            if self._editing_text_is_new:
                if not self.can_undo():
                    self._finish_inline_text_edit(accept=False)
                    return
                current_snapshot = self._make_snapshot()
                self._finish_inline_text_edit(accept=False)
                self._redo_stack.append(current_snapshot)
                snapshot = self._undo_stack.pop()
                self._restore_snapshot(snapshot)
                self.state.dirty = True
                self.changed.emit()
                self._refresh()
                return
            self._finish_inline_text_edit(accept=True)
        if not self.can_undo():
            return
        self._redo_stack.append(self._make_snapshot())
        snapshot = self._undo_stack.pop()
        self._restore_snapshot(snapshot)
        self.state.dirty = True
        self.changed.emit()
        self._refresh()

    def redo(self) -> None:
        if self._inline_text_editor is not None:
            self._finish_inline_text_edit(accept=True)
        if not self.can_redo():
            return
        self._undo_stack.append(self._make_snapshot())
        snapshot = self._redo_stack.pop()
        self._restore_snapshot(snapshot)
        self.state.dirty = True
        self.changed.emit()
        self._refresh()

    def rotate(self, angle: int) -> None:
        if self._image.isNull():
            return
        self._push_undo_state()
        old_size = self._image.size()
        transform = QTransform()
        transform.rotate(angle)
        self._image = self._image.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self._items = [self._rotated_item(item, angle % 360, old_size, self._image.size()) for item in self._items]
        self._mark_dirty()
        self._refresh()

    def scale_image(self, factor: float) -> None:
        if self._image.isNull() or factor <= 0:
            return
        self._push_undo_state()
        width = max(1, round(self._image.width() * factor))
        height = max(1, round(self._image.height() * factor))
        self._image = self._image.scaled(
            width,
            height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._items = [self._scaled_item(item, factor) for item in self._items]
        self._mark_dirty()
        self._refresh()

    def _mark_dirty(self) -> None:
        self.state.dirty = True
        self.changed.emit()

    def _push_undo_state(self) -> None:
        if self._image.isNull():
            return
        self._undo_stack.append(self._make_snapshot())
        self._redo_stack.clear()

    def _make_snapshot(self) -> CanvasSnapshot:
        return CanvasSnapshot(
            image=self._image.copy(),
            items=[item.clone() for item in self._items],
        )

    def _restore_snapshot(self, snapshot: CanvasSnapshot) -> None:
        self._image = snapshot.image.copy()
        self._items = [item.clone() for item in snapshot.items]
        self._clear_selection()
        self._drag_start = None
        self._active_handle = None

    def _compose_image(self) -> QImage:
        if self._image.isNull():
            return QImage()
        composed = self._image.copy()
        painter = QPainter(composed)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for item in self._items:
            self._draw_item(painter, item, selected=False)
        painter.end()
        return composed

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._inline_text_editor is not None:
            if not self._inline_text_editor.geometry().contains(event.position().toPoint()):
                self._finish_inline_text_edit(accept=True)
            event.accept()
            return
        if not self.has_image():
            return
        image_point = self._map_to_image(event.position().toPoint())
        if image_point is None:
            return

        if self._tool == Tool.SELECT:
            primary_index = self._primary_selected_index()
            if self.has_single_selected_item() and primary_index is not None:
                handle = self._find_handle_at(self._items[primary_index], image_point)
                if handle is not None:
                    self._active_handle = handle
                    self._drag_start = image_point
                    self._push_undo_state()
                    self._refresh()
                    return
            previous_selection = list(self._selected_item_indices)
            clicked_index = self._find_item_at(image_point)
            additive = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            self._active_handle = None
            if additive and clicked_index is not None:
                self._toggle_item_selection(clicked_index)
            else:
                self._select_single_item(clicked_index)
            primary_index = self._primary_selected_index()
            self._drag_start = image_point if self.has_selected_item() else None
            if self.has_single_selected_item() and primary_index is not None:
                self._active_handle = self._find_handle_at(self._items[primary_index], image_point)
                self._push_undo_state()
            elif self.has_selected_item():
                self._push_undo_state()
            if previous_selection != self._selected_item_indices:
                self.changed.emit()
            self._refresh()
            return

        if self._tool == Tool.NUMBER:
            item = self._build_click_item(self._tool, image_point)
            if item is not None:
                self._push_undo_state()
                self._items.append(item)
                self._select_single_item(len(self._items) - 1)
                self._mark_dirty()
                self._refresh()
            return

        if self._tool in (
            Tool.PEN,
            Tool.MARKER_PEN,
            Tool.LINE,
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.BLUR,
            Tool.PIXELATE,
            Tool.CROP,
        ):
            self._push_undo_state()
        self._preview_start = image_point
        self._preview_end = image_point
        self._last_point = image_point
        self._clear_selection()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._inline_text_editor is not None:
            event.accept()
            return
        if not self.has_image() or self._preview_start is None:
            image_point = self._map_to_image(event.position().toPoint())
            if self._tool == Tool.SELECT and self.has_selected_item() and self._drag_start is not None and image_point is not None:
                if self._active_handle is not None and self.has_single_selected_item():
                    item = self._primary_selected_item()
                    if item is not None:
                        self._resize_item(item, self._active_handle, image_point)
                else:
                    delta = image_point - self._drag_start
                    if delta.manhattanLength() > 0:
                        for index in self._selected_item_indices:
                            self._items[index].move_by(delta)
                        self._drag_start = image_point
                self._mark_dirty()
                self._refresh()
                self._update_cursor_for_point(image_point)
                return
            if self._tool == Tool.SELECT:
                self._update_cursor_for_point(image_point)
            return
        image_point = self._map_to_image(event.position().toPoint())
        if image_point is None:
            return

        if self._tool in (Tool.PEN, Tool.MARKER_PEN) and self._last_point is not None:
            painter = QPainter(self._image)
            pen_color = QColor(self._color)
            pen_width = self._pen_width
            if self._tool == Tool.MARKER_PEN:
                pen_color.setAlpha(110)
                pen_width = max(8, self._pen_width * 3)
            pen = QPen(pen_color, pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_point, image_point)
            painter.end()
            self._last_point = image_point
            self._mark_dirty()

        self._preview_end = image_point
        self._refresh()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._inline_text_editor is not None:
            event.accept()
            return
        if not self.has_image():
            return

        if self._tool == Tool.SELECT:
            if self._drag_start is not None or self._active_handle is not None:
                self._drag_start = None
                self._active_handle = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self._refresh()
            return

        if self._preview_start is None:
            return

        image_point = self._map_to_image(event.position().toPoint())
        if image_point is not None:
            self._preview_end = image_point

        if self._tool in (
            Tool.LINE,
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.BLUR,
            Tool.PIXELATE,
            Tool.CROP,
        ) and self._preview_end is not None:
            rect = QRect(self._preview_start, self._preview_end).normalized()
            item = self._build_drag_item(self._tool, QPoint(self._preview_start), QPoint(self._preview_end), rect)
            if item is not None:
                self._items.append(item)
                self._select_single_item(len(self._items) - 1)
                if self._tool == Tool.TEXT:
                    self._start_inline_text_edit(len(self._items) - 1, is_new=True)
            elif self._tool == Tool.CROP:
                self._image = self._image.copy(rect)
                self._clear_selection()
            elif self._tool in (Tool.BLUR, Tool.PIXELATE):
                self._apply_region_effect(rect, self._tool)
                self._clear_selection()
            if item is not None or self._tool in (Tool.CROP, Tool.BLUR, Tool.PIXELATE):
                self._mark_dirty()

        self._preview_start = None
        self._preview_end = None
        self._last_point = None
        self._drag_start = None
        self._active_handle = None
        self._refresh()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.has_image() or self._tool != Tool.SELECT:
            super().mouseDoubleClickEvent(event)
            return
        image_point = self._map_to_image(event.position().toPoint())
        if image_point is None:
            super().mouseDoubleClickEvent(event)
            return
        clicked_index = self._find_item_at(image_point)
        if clicked_index is None:
            super().mouseDoubleClickEvent(event)
            return
        self._select_single_item(clicked_index)
        item = self._primary_selected_item()
        if item is not None and item.kind == Tool.TEXT:
            self.edit_selected_text(self)
        else:
            self.changed.emit()
            self._refresh()

    def _refresh(self) -> None:
        if self._image.isNull():
            self.clear()
            self.setText("Take a screenshot or open an image.")
            self.resize(self.minimumSize())
            return

        zoom_factor = self._zoom_percent / 100.0
        display_width = max(1, round(self._image.width() * zoom_factor))
        display_height = max(1, round(self._image.height() * zoom_factor))
        display = QPixmap.fromImage(self._image).scaled(
            display_width,
            display_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        sx = display_width / self._image.width() if self._image.width() else 1
        sy = display_height / self._image.height() if self._image.height() else 1
        painter = QPainter(display)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for index, item in enumerate(self._items):
            self._draw_item_preview(painter, item, sx, sy, selected=index in self._selected_item_indices, show_handles=index == self._primary_selected_index() and self.has_single_selected_item())

        if self._tool in (
            Tool.LINE,
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.BLUR,
            Tool.PIXELATE,
            Tool.CROP,
        ) and self._preview_start is not None and self._preview_end is not None:
            pen = QPen(self._color, max(1, self._pen_width))
            painter.setPen(pen)
            start_point, end_point = self._display_points()
            rect = QRect(start_point, end_point).normalized()
            if self._tool == Tool.LINE:
                painter.drawLine(start_point, end_point)
            elif self._tool == Tool.ARROW:
                self._draw_arrow(painter, start_point, end_point)
            elif self._tool == Tool.DOUBLE_ARROW:
                self._draw_double_arrow(painter, start_point, end_point)
            elif self._tool in (Tool.RECT, Tool.CROP, Tool.BLUR, Tool.PIXELATE, Tool.TEXT, Tool.TEXT_POINTER, Tool.NUMBER_POINTER, Tool.MARKER_RECT):
                painter.drawRect(rect)
            elif self._tool in (Tool.ELLIPSE, Tool.MARKER_ELLIPSE):
                painter.drawEllipse(rect)
            if self._tool in (Tool.BLUR, Tool.PIXELATE, Tool.CROP):
                painter.fillRect(rect, QColor(255, 255, 255, 40))
        painter.end()

        self.setPixmap(display)
        self.resize(display.size())
        if self._inline_text_editor is not None and self._editing_text_index is not None and 0 <= self._editing_text_index < len(self._items):
            self._sync_inline_text_editor_style(self._items[self._editing_text_index])
            self._sync_inline_text_editor_geometry()

    def _display_points(self) -> tuple[QPoint, QPoint]:
        sx = self._zoom_percent / 100.0
        sy = self._zoom_percent / 100.0
        start = QPoint(int(self._preview_start.x() * sx), int(self._preview_start.y() * sy))
        end = QPoint(int(self._preview_end.x() * sx), int(self._preview_end.y() * sy))
        return start, end

    def _image_rect_in_widget(self) -> QRect | None:
        if self._image.isNull() or self.width() <= 0 or self.height() <= 0:
            return None
        return QRect(0, 0, self.width(), self.height())

    def _map_to_image(self, point: QPoint) -> QPoint | None:
        image_rect = self._image_rect_in_widget()
        if image_rect is None or not image_rect.contains(point):
            return None

        x = point.x() - image_rect.x()
        y = point.y() - image_rect.y()
        image_x = round(x * self._image.width() / image_rect.width())
        image_y = round(y * self._image.height() / image_rect.height())
        image_x = max(0, min(self._image.width() - 1, image_x))
        image_y = max(0, min(self._image.height() - 1, image_y))
        return QPoint(image_x, image_y)

    def _find_item_at(self, point: QPoint) -> int | None:
        for index in range(len(self._items) - 1, -1, -1):
            item = self._items[index]
            if item.kind == Tool.LINE:
                if self._point_line_distance(point, item.start, item.end) <= max(6, item.pen_width * 2):
                    return index
            elif item.kind in (Tool.ARROW, Tool.DOUBLE_ARROW, Tool.TEXT_ARROW, Tool.NUMBER_ARROW):
                if self._point_line_distance(point, item.start, item.end) <= max(8, item.pen_width * 2):
                    return index
            elif item.bounds().contains(point):
                return index
        return None

    def _point_line_distance(self, point: QPoint, start: QPoint, end: QPoint) -> float:
        px, py = point.x(), point.y()
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return hypot(px - proj_x, py - proj_y)

    def _draw_item(self, painter: QPainter, item: OverlayItem, selected: bool, show_handles: bool = True) -> None:
        if item.shadow:
            self._draw_shadow(painter, item)
        painter.save()
        painter.setOpacity(item.opacity)
        pen_color = item.color if self._has_border(item.fill_mode) else QColor(item.color.red(), item.color.green(), item.color.blue(), 0)
        pen = QPen(pen_color, item.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        if item.kind == Tool.LINE:
            painter.drawLine(item.start, item.end)
        elif item.kind == Tool.ARROW:
            self._draw_arrow(painter, item.start, item.end, color=item.color, pen_width=item.pen_width)
        elif item.kind == Tool.DOUBLE_ARROW:
            self._draw_double_arrow(painter, item.start, item.end, color=item.color, pen_width=item.pen_width)
        elif item.kind in (Tool.RECT, Tool.MARKER_RECT):
            if item.kind == Tool.MARKER_RECT:
                pen = QPen(item.color, max(item.pen_width * 3, 8), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
            painter.setBrush(self._brush_for_item(item))
            painter.drawRect(QRect(item.start, item.end).normalized())
        elif item.kind in (Tool.ELLIPSE, Tool.MARKER_ELLIPSE):
            if item.kind == Tool.MARKER_ELLIPSE:
                pen = QPen(item.color, max(item.pen_width * 3, 8), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
            painter.setBrush(self._brush_for_item(item))
            painter.drawEllipse(QRect(item.start, item.end).normalized())
        elif item.kind == Tool.TEXT:
            font = self._text_font(item)
            text_box = item.bounds().adjusted(2, 2, -2, -2)
            if self._has_fill(item.fill_mode):
                painter.setBrush(item.color)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            if self._has_border(item.fill_mode):
                painter.drawRoundedRect(text_box, 6, 6)
            painter.setFont(font)
            painter.setPen(QPen(item.text_color or item.color, max(1, item.pen_width // 2)))
            painter.drawText(
                text_box.adjusted(8, 4, -8, -4),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                item.text or "",
            )
        elif item.kind == Tool.TEXT_POINTER:
            self._draw_text_pointer(painter, item)
        elif item.kind == Tool.TEXT_ARROW:
            self._draw_text_arrow(painter, item)
        elif item.kind == Tool.NUMBER:
            self._draw_number_badge(painter, item)
        elif item.kind == Tool.NUMBER_POINTER:
            self._draw_number_pointer(painter, item)
        elif item.kind == Tool.NUMBER_ARROW:
            self._draw_number_arrow(painter, item)
        elif item.kind == Tool.IMAGE and item.image is not None and not item.image.isNull():
            painter.drawImage(QRect(item.start, item.end).normalized(), item.image)
        elif item.kind == Tool.STICKER and item.image is not None and not item.image.isNull():
            painter.drawImage(QRect(item.start, item.end).normalized(), item.image)
        painter.restore()

        if selected:
            selection_pen = QPen(QColor("#1c7ed6"), 1, Qt.PenStyle.DashLine)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(item.bounds())
            if show_handles:
                self._draw_selection_handles(painter, item)

    def _draw_item_preview(self, painter: QPainter, item: OverlayItem, sx: float, sy: float, selected: bool, show_handles: bool = True) -> None:
        scaled = item.clone()
        scaled.start = QPoint(int(item.start.x() * sx), int(item.start.y() * sy))
        scaled.end = QPoint(int(item.end.x() * sx), int(item.end.y() * sy))
        scaled.pen_width = max(1, int(item.pen_width * max(sx, sy)))
        self._draw_item(painter, scaled, selected, show_handles=show_handles)

    def delete_selected_item(self) -> bool:
        if not self.has_selected_item():
            return False
        self._push_undo_state()
        for index in sorted(self._selected_item_indices, reverse=True):
            del self._items[index]
        self._clear_selection()
        self._drag_start = None
        self._mark_dirty()
        self._refresh()
        return True

    def duplicate_selected_item(self) -> bool:
        if not self.has_selected_item():
            return False
        self._push_undo_state()
        new_indices: list[int] = []
        for index in self._selected_item_indices:
            duplicated = self._items[index].clone()
            duplicated.move_by(QPoint(12, 12))
            self._items.append(duplicated)
            new_indices.append(len(self._items) - 1)
        self._selected_item_indices = new_indices
        self._primary_selected_item_index = new_indices[-1] if new_indices else None
        self._drag_start = None
        self._active_handle = None
        self._mark_dirty()
        self._refresh()
        return True

    def copy_selected_item_to_clipboard(self) -> bool:
        if not self.has_selected_item():
            return False
        # Access QApplication lazily here to avoid widening imports for non-GUI tests.
        from PyQt6.QtGui import QGuiApplication

        payload = {
            "type": "ksnip_py.overlay_items",
            "items": [self._serialize_item(self._items[index]) for index in self._selected_item_indices],
        }
        QGuiApplication.clipboard().setText(json.dumps(payload))
        return True

    def paste_item_from_clipboard(self) -> bool:
        from PyQt6.QtGui import QGuiApplication

        raw = QGuiApplication.clipboard().text()
        if not raw:
            return False
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return False
        if payload.get("type") not in {"ksnip_py.overlay_item", "ksnip_py.overlay_items"}:
            return False
        self._push_undo_state()
        items_payload = payload.get("items")
        if items_payload is None:
            items_payload = [payload["item"]]
        new_indices: list[int] = []
        for item_payload in items_payload:
            item = self._deserialize_item(item_payload)
            item.move_by(QPoint(12, 12))
            self._items.append(item)
            new_indices.append(len(self._items) - 1)
        self._selected_item_indices = new_indices
        self._primary_selected_item_index = new_indices[-1] if new_indices else None
        self._drag_start = None
        self._active_handle = None
        self._mark_dirty()
        self._refresh()
        return True

    def bring_selected_item_to_front(self) -> bool:
        if not self.has_selected_item():
            return False
        if not self.can_bring_selected_item_to_front():
            return False
        self._push_undo_state()
        selected = {index: self._items[index] for index in self._selected_item_indices}
        remaining = [item for index, item in enumerate(self._items) if index not in selected]
        ordered_selected = [selected[index] for index in self._selected_item_indices]
        self._items = remaining + ordered_selected
        start = len(remaining)
        self._selected_item_indices = list(range(start, len(self._items)))
        self._primary_selected_item_index = self._selected_item_indices[-1]
        self._drag_start = None
        self._active_handle = None
        self._mark_dirty()
        self._refresh()
        return True

    def send_selected_item_to_back(self) -> bool:
        if not self.has_selected_item():
            return False
        if not self.can_send_selected_item_to_back():
            return False
        self._push_undo_state()
        selected = {index: self._items[index] for index in self._selected_item_indices}
        remaining = [item for index, item in enumerate(self._items) if index not in selected]
        ordered_selected = [selected[index] for index in self._selected_item_indices]
        self._items = ordered_selected + remaining
        self._selected_item_indices = list(range(len(ordered_selected)))
        self._primary_selected_item_index = self._selected_item_indices[-1]
        self._drag_start = None
        self._active_handle = None
        self._mark_dirty()
        self._refresh()
        return True

    def can_bring_selected_item_to_front(self) -> bool:
        return self.has_selected_item() and max(self._selected_item_indices) < len(self._items) - 1

    def can_send_selected_item_to_back(self) -> bool:
        return self.has_selected_item() and min(self._selected_item_indices) > 0

    def edit_selected_text(self, parent=None) -> bool:
        item = self._primary_selected_item()
        if not self.has_single_selected_item() or item is None or item.kind != Tool.TEXT:
            return False
        primary_index = self._primary_selected_index()
        if primary_index is None:
            return False
        return self._start_inline_text_edit(primary_index, is_new=False, select_all=True)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:  # noqa: N802
        if self._inline_text_editor is not None:
            super().contextMenuEvent(event)
            return
        if not self.has_image():
            super().contextMenuEvent(event)
            return
        image_point = self._map_to_image(event.pos())
        if image_point is None:
            super().contextMenuEvent(event)
            return
        clicked_index = self._find_item_at(image_point)
        if clicked_index is None:
            super().contextMenuEvent(event)
            return
        self._select_single_item(clicked_index)
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.TEXT:
            super().contextMenuEvent(event)
            return
        menu = QMenu(self)
        edit_action = QAction("Edit text", menu)
        edit_action.triggered.connect(lambda: self.edit_selected_text(self))
        menu.addAction(edit_action)
        menu.exec(event.globalPos())

    def apply_font_family_to_selected_text(self, family: str) -> bool:
        item = self._primary_selected_item()
        if not self.has_single_selected_item() or item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return False
        if item.font_family == family:
            return False
        self._push_undo_state()
        item.font_family = family
        self._mark_dirty()
        self._refresh()
        return True

    def apply_font_point_size_to_selected_text(self, point_size: int) -> bool:
        item = self._primary_selected_item()
        if not self.has_single_selected_item() or item is None or not (self._is_text_like(item.kind) or self._is_number_like(item.kind)):
            return False
        point_size = max(1, point_size)
        if item.font_point_size == point_size:
            return False
        self._push_undo_state()
        item.font_point_size = point_size
        self._mark_dirty()
        self._refresh()
        return True

    def apply_color_to_selected_item(self, color: QColor) -> bool:
        if not self.has_selected_item():
            return False
        if all(self._items[index].color == color for index in self._selected_item_indices):
            return False
        self._push_undo_state()
        for index in self._selected_item_indices:
            self._items[index].color = QColor(color)
        self._mark_dirty()
        self._refresh()
        return True

    def apply_pen_width_to_selected_item(self, width: int) -> bool:
        if not self.has_selected_item():
            return False
        width = max(1, width)
        if all(self._items[index].pen_width == width for index in self._selected_item_indices):
            return False
        self._push_undo_state()
        for index in self._selected_item_indices:
            self._items[index].pen_width = width
        self._mark_dirty()
        self._refresh()
        return True

    def apply_fill_color_to_selected_item(self, color: QColor) -> bool:
        shape_indices = [
            index
            for index in self._selected_item_indices
            if self._items[index].kind in (Tool.RECT, Tool.ELLIPSE)
        ]
        if not shape_indices:
            return False
        if all(self._items[index].fill_color == color for index in shape_indices):
            return False
        self._push_undo_state()
        for index in shape_indices:
            self._items[index].fill_color = QColor(color)
        self._mark_dirty()
        self._refresh()
        return True

    def apply_text_color_to_selected_item(self, color: QColor) -> bool:
        text_indices = [
            index
            for index in self._selected_item_indices
            if self._is_text_like(self._items[index].kind) or self._is_number_like(self._items[index].kind)
        ]
        if not text_indices:
            return False
        if all(self._items[index].text_color == color for index in text_indices):
            return False
        self._push_undo_state()
        for index in text_indices:
            self._items[index].text_color = QColor(color)
        self._mark_dirty()
        self._refresh()
        return True

    def apply_opacity_to_selected_item(self, opacity_percent: int) -> bool:
        if not self.has_selected_item():
            return False
        opacity = max(0.0, min(1.0, opacity_percent / 100.0))
        if all(abs(self._items[index].opacity - opacity) < 0.001 for index in self._selected_item_indices):
            return False
        self._push_undo_state()
        for index in self._selected_item_indices:
            self._items[index].opacity = opacity
        self._mark_dirty()
        self._refresh()
        return True

    def apply_fill_mode_to_selected_item(self, fill_mode: FillMode) -> bool:
        shape_indices = [
            index
            for index in self._selected_item_indices
            if self._items[index].kind in (Tool.RECT, Tool.ELLIPSE, Tool.TEXT, Tool.TEXT_ARROW, Tool.NUMBER, Tool.NUMBER_ARROW)
        ]
        if not shape_indices:
            return False
        if all(self._items[index].fill_mode == fill_mode for index in shape_indices):
            return False
        self._push_undo_state()
        for index in shape_indices:
            self._items[index].fill_mode = fill_mode
        self._mark_dirty()
        self._refresh()
        return True

    def apply_bold_to_selected_text(self, bold: bool) -> bool:
        text_indices = [
            index
            for index in self._selected_item_indices
            if self._is_text_like(self._items[index].kind) or self._is_number_like(self._items[index].kind)
        ]
        if not text_indices:
            return False
        if all(self._items[index].bold == bold for index in text_indices):
            return False
        self._push_undo_state()
        for index in text_indices:
            self._items[index].bold = bold
        self._mark_dirty()
        self._refresh()
        return True

    def apply_italic_to_selected_text(self, italic: bool) -> bool:
        text_indices = [
            index
            for index in self._selected_item_indices
            if self._is_text_like(self._items[index].kind) or self._is_number_like(self._items[index].kind)
        ]
        if not text_indices:
            return False
        if all(self._items[index].italic == italic for index in text_indices):
            return False
        self._push_undo_state()
        for index in text_indices:
            self._items[index].italic = italic
        self._mark_dirty()
        self._refresh()
        return True

    def apply_underline_to_selected_text(self, underline: bool) -> bool:
        text_indices = [
            index
            for index in self._selected_item_indices
            if self._is_text_like(self._items[index].kind) or self._is_number_like(self._items[index].kind)
        ]
        if not text_indices:
            return False
        if all(self._items[index].underline == underline for index in text_indices):
            return False
        self._push_undo_state()
        for index in text_indices:
            self._items[index].underline = underline
        self._mark_dirty()
        self._refresh()
        return True

    def apply_shadow_to_selected_item(self, shadow: bool) -> bool:
        if not self.has_selected_item():
            return False
        if all(self._items[index].shadow == shadow for index in self._selected_item_indices):
            return False
        self._push_undo_state()
        for index in self._selected_item_indices:
            self._items[index].shadow = shadow
        self._mark_dirty()
        self._refresh()
        return True

    def apply_scaling_to_selected_item(self, scaling_percent: int) -> bool:
        item_indices = [
            index for index in self._selected_item_indices if self._items[index].kind in (Tool.IMAGE, Tool.STICKER)
        ]
        if not item_indices:
            return False
        scaling = max(0.0, scaling_percent / 100.0)
        if all(abs(self._items[index].scaling - scaling) < 0.001 for index in item_indices):
            return False
        self._push_undo_state()
        for index in item_indices:
            item = self._items[index]
            rect = QRect(item.start, item.end).normalized()
            center = rect.center()
            new_width = max(8, round(rect.width() * scaling / max(item.scaling, 0.01)))
            new_height = max(8, round(rect.height() * scaling / max(item.scaling, 0.01)))
            item.start = QPoint(center.x() - new_width // 2, center.y() - new_height // 2)
            item.end = QPoint(item.start.x() + new_width, item.start.y() + new_height)
            item.scaling = scaling
        self._mark_dirty()
        self._refresh()
        return True

    def apply_number_to_selected_item(self, value: int) -> bool:
        item = self._primary_selected_item()
        if item is None or not self._is_number_like(item.kind):
            return False
        resolved = max(1, int(value))
        if item.text == str(resolved):
            return False
        self._push_undo_state()
        item.text = str(resolved)
        self._mark_dirty()
        self._refresh()
        return True

    def apply_sticker_to_selected_item(self, sticker_path: str) -> bool:
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.STICKER:
            return False
        image = self._load_sticker_image(sticker_path)
        if image is None or image.isNull() or item.sticker_path == sticker_path:
            return False
        self._push_undo_state()
        item.sticker_path = sticker_path
        item.image = image
        self._mark_dirty()
        self._refresh()
        return True

    def _brush_for_item(self, item: OverlayItem):
        if not self._has_fill(item.fill_mode):
            return Qt.BrushStyle.NoBrush
        return item.color

    def _find_handle_at(self, item: OverlayItem, point: QPoint) -> str | None:
        for handle_name, handle_point in self._handle_points(item).items():
            radius = 9 if item.kind == Tool.TEXT else 6
            if QRect(handle_point.x() - radius, handle_point.y() - radius, radius * 2, radius * 2).contains(point):
                return handle_name
        return None

    def _draw_selection_handles(self, painter: QPainter, item: OverlayItem) -> None:
        if item.kind == Tool.TEXT:
            painter.save()
            painter.setPen(QPen(QColor("#1c7ed6"), 1))
            for handle_point in self._handle_points(item).values():
                outer = QRect(handle_point.x() - 6, handle_point.y() - 6, 12, 12)
                inner = QRect(handle_point.x() - 3, handle_point.y() - 3, 6, 6)
                painter.setBrush(QColor("#ffffff"))
                painter.drawEllipse(outer)
                painter.setBrush(QColor("#1c7ed6"))
                painter.drawEllipse(inner)
            painter.restore()
            return
        painter.save()
        painter.setBrush(QColor("#1c7ed6"))
        for handle_point in self._handle_points(item).values():
            painter.drawRect(QRect(handle_point.x() - 3, handle_point.y() - 3, 6, 6))
        painter.restore()

    def _update_cursor_for_point(self, point: QPoint | None) -> None:
        if self._tool != Tool.SELECT or point is None or not self.has_single_selected_item():
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        item = self._primary_selected_item()
        if item is None:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        handle = self._find_handle_at(item, point)
        if handle in {"top_left", "bottom_right"}:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            return
        if handle in {"top_right", "bottom_left"}:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            return
        if handle in {"top", "bottom"}:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            return
        if handle in {"left", "right"}:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return
        if item.bounds().contains(point):
            self.setCursor(Qt.CursorShape.SizeAllCursor)
            return
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def _handle_points(self, item: OverlayItem) -> dict[str, QPoint]:
        if self._is_line_like(item.kind):
            return {
                "start": QPoint(item.start),
                "end": QPoint(item.end),
            }

        if item.kind in (
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
            Tool.TEXT_POINTER,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
        ):
            rect = QRect(item.start, item.end).normalized()
            return {
                "top_left": rect.topLeft(),
                "top_right": rect.topRight(),
                "bottom_left": rect.bottomLeft(),
                "bottom_right": rect.bottomRight(),
            }

        if item.kind == Tool.IMAGE:
            rect = QRect(item.start, item.end).normalized()
            return {
                "top_left": rect.topLeft(),
                "top_right": rect.topRight(),
                "bottom_left": rect.bottomLeft(),
                "bottom_right": rect.bottomRight(),
            }

        bounds = item.bounds()
        if item.kind == Tool.TEXT:
            return {
                "top_left": bounds.topLeft(),
                "top": QPoint(bounds.center().x(), bounds.top()),
                "top_right": bounds.topRight(),
                "left": QPoint(bounds.left(), bounds.center().y()),
                "right": QPoint(bounds.right(), bounds.center().y()),
                "bottom_left": bounds.bottomLeft(),
                "bottom": QPoint(bounds.center().x(), bounds.bottom()),
                "bottom_right": bounds.bottomRight(),
            }
        return {
            "top_left": bounds.topLeft(),
            "top_right": bounds.topRight(),
            "bottom_left": bounds.bottomLeft(),
            "bottom_right": bounds.bottomRight(),
        }

    def _resize_item(self, item: OverlayItem, handle: str, point: QPoint) -> None:
        if self._is_line_like(item.kind):
            if handle == "start":
                item.start = QPoint(point)
            elif handle == "end":
                item.end = QPoint(point)
            return

        if item.kind == Tool.TEXT:
            rect = QRect(item.start, item.end).normalized()
            if handle == "top_left":
                rect.setTopLeft(point)
            elif handle == "top":
                rect.setTop(point.y())
            elif handle == "top_right":
                rect.setTopRight(point)
            elif handle == "left":
                rect.setLeft(point.x())
            elif handle == "right":
                rect.setRight(point.x())
            elif handle == "bottom_left":
                rect.setBottomLeft(point)
            elif handle == "bottom":
                rect.setBottom(point.y())
            elif handle == "bottom_right":
                rect.setBottomRight(point)
            rect = rect.normalized()
            min_width, min_height = self._text_natural_size(item)
            if rect.width() < min_width:
                if handle in {"top_left", "left", "bottom_left"}:
                    rect.setLeft(rect.right() - min_width)
                else:
                    rect.setRight(rect.left() + min_width)
            if rect.height() < min_height:
                if handle in {"top_left", "top", "top_right"}:
                    rect.setTop(rect.bottom() - min_height)
                else:
                    rect.setBottom(rect.top() + min_height)
            item.start = rect.topLeft()
            item.end = rect.bottomRight()
            return

        rect = QRect(item.start, item.end).normalized()
        if handle == "top_left":
            rect.setTopLeft(point)
        elif handle == "top_right":
            rect.setTopRight(point)
        elif handle == "bottom_left":
            rect.setBottomLeft(point)
        elif handle == "bottom_right":
            rect.setBottomRight(point)
        rect = rect.normalized()
        item.start = rect.topLeft()
        item.end = rect.bottomRight()

    def _scaled_item(self, item: OverlayItem, factor: float) -> OverlayItem:
        scaled = item.clone()
        scaled.start = QPoint(round(item.start.x() * factor), round(item.start.y() * factor))
        scaled.end = QPoint(round(item.end.x() * factor), round(item.end.y() * factor))
        scaled.pen_width = max(1, round(item.pen_width * factor))
        return scaled

    def _rotated_item(self, item: OverlayItem, angle: int, old_size, new_size) -> OverlayItem:
        rotated = item.clone()
        rotated.start = self._rotate_point(item.start, angle, old_size, new_size)
        rotated.end = self._rotate_point(item.end, angle, old_size, new_size)
        return rotated

    def _rotate_point(self, point: QPoint, angle: int, old_size, new_size) -> QPoint:
        x = point.x()
        y = point.y()
        if angle == 90:
            return QPoint(new_size.width() - 1 - y, x)
        if angle == 180:
            return QPoint(new_size.width() - 1 - x, new_size.height() - 1 - y)
        if angle == 270:
            return QPoint(y, new_size.height() - 1 - x)
        return QPoint(x, y)

    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor | None = None, pen_width: int | None = None) -> None:
        painter.drawLine(start, end)
        self._draw_arrow_head(painter, start, end, color=color, pen_width=pen_width)

    def _draw_arrow_head(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor | None = None, pen_width: int | None = None) -> None:
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        if dx == 0 and dy == 0:
            return

        length = (dx * dx + dy * dy) ** 0.5
        ux = dx / length
        uy = dy / length
        resolved_pen_width = self._pen_width if pen_width is None else pen_width
        arrow_size = max(12, resolved_pen_width * 5)
        px = -uy
        py = ux

        left = QPoint(
            int(end.x() - ux * arrow_size + px * arrow_size * 0.5),
            int(end.y() - uy * arrow_size + py * arrow_size * 0.5),
        )
        right = QPoint(
            int(end.x() - ux * arrow_size - px * arrow_size * 0.5),
            int(end.y() - uy * arrow_size - py * arrow_size * 0.5),
        )
        polygon = QPolygon([end, left, right])
        painter.setBrush(self._color if color is None else color)
        painter.drawPolygon(polygon)

    def _draw_double_arrow(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor | None = None, pen_width: int | None = None) -> None:
        painter.drawLine(start, end)
        self._draw_arrow_head(painter, start, end, color=color, pen_width=pen_width)
        self._draw_arrow_head(painter, end, start, color=color, pen_width=pen_width)

    def _text_font(self, item: OverlayItem) -> QFont:
        font = QFont()
        if item.font_family:
            font.setFamily(item.font_family)
        font.setPointSize(item.font_point_size or max(10, item.pen_width * 4))
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        return font

    def _text_natural_size(self, item: OverlayItem) -> tuple[int, int]:
        lines = (item.text or "").splitlines() or [""]
        metrics = QFontMetrics(self._text_font(item))
        width = max(60, max(metrics.horizontalAdvance(line or " ") for line in lines) + 18)
        height = max(28, metrics.lineSpacing() * len(lines) + 10)
        return width, height

    def _item_display_rect(self, item: OverlayItem) -> QRect:
        sx = self._zoom_percent / 100.0
        sy = self._zoom_percent / 100.0
        bounds = item.bounds()
        left = int(bounds.left() * sx)
        top = int(bounds.top() * sy)
        width = max(40, int(bounds.width() * sx))
        height = max(28, int(bounds.height() * sy))
        return QRect(left, top, width, height)

    def _sync_inline_text_editor_geometry(self) -> None:
        if self._inline_text_editor is None or self._editing_text_index is None:
            return
        if not (0 <= self._editing_text_index < len(self._items)):
            return
        item = self._items[self._editing_text_index]
        rect = self._item_display_rect(item).adjusted(2, 2, -2, -2)
        self._inline_text_editor.setGeometry(rect)

    @staticmethod
    def _color_to_css(color: QColor) -> str:
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alphaF():.3f})"

    def _sync_inline_text_editor_style(self, item: OverlayItem) -> None:
        if self._inline_text_editor is None:
            return
        border_color = QColor(item.color)
        border_color.setAlpha(255)
        border = f"1px solid {self._color_to_css(border_color)}" if self._has_border(item.fill_mode) else "1px dashed rgba(176, 176, 176, 0.95)"
        background_color = QColor(item.color) if self._has_fill(item.fill_mode) else QColor(255, 255, 255, 0)
        text_color = QColor(item.text_color or item.color)
        selection_background = QColor(item.color)
        selection_background.setAlpha(180)
        self._inline_text_editor.setFont(self._text_font(item))
        self._inline_text_editor.set_spellcheck_color_scheme(load_spellcheck_scheme())
        self._inline_text_editor.set_spellcheck_reference_color(item.color)
        palette = self._inline_text_editor.palette()
        palette.setColor(QPalette.ColorRole.Base, background_color)
        palette.setColor(QPalette.ColorRole.Text, text_color)
        palette.setColor(QPalette.ColorRole.Highlight, selection_background)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self._inline_text_editor.setPalette(palette)
        self._inline_text_editor.viewport().setAutoFillBackground(True)
        self._inline_text_editor.setAutoFillBackground(True)
        self._inline_text_editor.setStyleSheet(
            "QPlainTextEdit {"
            f"background-color: {self._color_to_css(background_color)};"
            f"color: {self._color_to_css(text_color)};"
            f"border: {border};"
            "padding: 4px 8px;"
            f"selection-background-color: {self._color_to_css(selection_background)};"
            "selection-color: rgba(255, 255, 255, 1.0);"
            "}"
        )
        self._inline_text_editor.viewport().setStyleSheet(
            f"background-color: {self._color_to_css(background_color)};"
            f"color: {self._color_to_css(text_color)};"
        )

    def _start_inline_text_edit(self, index: int, *, is_new: bool = False, select_all: bool = False) -> bool:
        if not (0 <= index < len(self._items)):
            return False
        item = self._items[index]
        if item.kind != Tool.TEXT:
            return False
        self._finish_inline_text_edit(accept=True)
        editor = InlineTextEditor(self)
        editor.setFrameStyle(0)
        editor.setLineWrapMode(SpellCheckTextEdit.LineWrapMode.WidgetWidth)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        editor.setPlainText(item.text or "")
        self._inline_text_editor = editor
        self._editing_text_index = index
        self._editing_text_original = item.text or ""
        self._editing_text_is_new = is_new
        self._sync_inline_text_editor_style(item)
        self._sync_inline_text_editor_geometry()
        editor.accepted.connect(lambda: self._finish_inline_text_edit(accept=True))
        editor.canceled.connect(lambda: self._finish_inline_text_edit(accept=False))
        editor.undo_requested.connect(self.undo)
        editor.redo_requested.connect(self.redo)
        editor.show()
        editor.setFocus()
        if select_all:
            editor.selectAll()
        return True

    def _finish_inline_text_edit(self, *, accept: bool) -> bool:
        editor = self._inline_text_editor
        index = self._editing_text_index
        original_text = self._editing_text_original or ""
        is_new = self._editing_text_is_new
        if editor is None or index is None:
            return False
        self._inline_text_editor = None
        self._editing_text_index = None
        self._editing_text_original = None
        self._editing_text_is_new = False
        text = editor.toPlainText()
        editor.hide()
        editor.deleteLater()
        if not (0 <= index < len(self._items)):
            self._refresh()
            return False
        item = self._items[index]
        if not accept:
            if is_new:
                del self._items[index]
                self._clear_selection()
            self._refresh()
            return False
        if not text.strip():
            if is_new:
                del self._items[index]
                self._clear_selection()
                self._refresh()
                return False
            text = original_text
        if not is_new and text == original_text:
            self._refresh()
            return False
        if not is_new:
            self._push_undo_state()
        item.text = text
        rect = QRect(item.start, item.end).normalized()
        width, height = self._text_natural_size(item)
        item.end = QPoint(max(rect.right(), item.start.x() + width), max(rect.bottom(), item.start.y() + height))
        self._select_single_item(index)
        self._mark_dirty()
        self._refresh()
        return True

    def _build_click_item(self, tool: Tool, point: QPoint) -> OverlayItem | None:
        if tool == Tool.TEXT:
            dialog = TextInputDialog(self, title="Insert text")
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            text = dialog.text()
            if not text:
                return None
            temp_item = OverlayItem(
                kind=Tool.TEXT,
                start=QPoint(point),
                end=QPoint(point),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=text,
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
                fill_mode=self._fill_mode,
            )
            width, height = self._text_natural_size(temp_item)
            return OverlayItem(
                kind=Tool.TEXT,
                start=QPoint(point),
                end=QPoint(point.x() + width, point.y() + height),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=text,
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
                fill_mode=self._fill_mode,
            )
        if tool == Tool.NUMBER:
            radius = max(16, self._font_point_size)
            value = self._next_number_value()
            return OverlayItem(
                kind=Tool.NUMBER,
                start=QPoint(point.x() - radius, point.y() - radius),
                end=QPoint(point.x() + radius, point.y() + radius),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=str(value),
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=True,
                italic=False,
                underline=self._underline,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
                fill_mode=self._fill_mode,
            )
        if tool == Tool.STICKER:
            image = self._load_sticker_image(self._sticker_path)
            if image is None or image.isNull():
                return None
            width = max(32, round(image.width() * self._scaling))
            height = max(32, round(image.height() * self._scaling))
            top_left = QPoint(point.x() - width // 2, point.y() - height // 2)
            return OverlayItem(
                kind=Tool.STICKER,
                start=top_left,
                end=QPoint(top_left.x() + width, top_left.y() + height),
                color=QColor(self._color),
                pen_width=self._pen_width,
                opacity=self._opacity,
                shadow=self._shadow,
                scaling=self._scaling,
                sticker_path=self._sticker_path,
                image=image,
            )
        return None

    def _build_drag_item(self, tool: Tool, start: QPoint, end: QPoint, rect: QRect) -> OverlayItem | None:
        if self._is_line_like(tool) or self._is_shape_like(tool):
            pen_width = self._pen_width
            color = QColor(self._color)
            fill_color = QColor(self._fill_color) if tool in (Tool.RECT, Tool.ELLIPSE) else None
            fill_mode = self._fill_mode
            if tool in (Tool.MARKER_RECT, Tool.MARKER_ELLIPSE):
                color.setAlpha(110)
                pen_width = max(8, self._pen_width * 3)
                fill_color = None
                fill_mode = FillMode.BORDER_AND_NO_FILL
            return OverlayItem(
                kind=tool,
                start=QPoint(start),
                end=QPoint(end),
                color=color,
                pen_width=pen_width,
                fill_color=fill_color,
                opacity=self._opacity,
                fill_mode=fill_mode,
            )
        if tool == Tool.TEXT:
            top_left = rect.topLeft()
            width = max(60, rect.width())
            height = max(28, rect.height())
            return OverlayItem(
                kind=Tool.TEXT,
                start=QPoint(top_left),
                end=QPoint(top_left.x() + width, top_left.y() + height),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text="",
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
                fill_mode=self._fill_mode,
            )
        if tool == Tool.TEXT_POINTER:
            dialog = TextInputDialog(self, title="Insert text")
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            text = dialog.text()
            if not text:
                return None
            return OverlayItem(
                kind=tool,
                start=rect.topLeft(),
                end=rect.bottomRight(),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=text,
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                fill_color=QColor(255, 255, 255, 220),
                fill_mode=FillMode.BORDER_AND_FILL,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
            )
        if tool == Tool.TEXT_ARROW:
            dialog = TextInputDialog(self, title="Insert text")
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return None
            text = dialog.text()
            if not text:
                return None
            return OverlayItem(
                kind=tool,
                start=QPoint(start),
                end=QPoint(end),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=text,
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=self._bold,
                italic=self._italic,
                underline=self._underline,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
                fill_mode=self._fill_mode,
            )
        if tool in (Tool.NUMBER_POINTER, Tool.NUMBER_ARROW):
            value = self._next_number_value()
            return OverlayItem(
                kind=tool,
                start=QPoint(start if tool == Tool.NUMBER_ARROW else rect.topLeft()),
                end=QPoint(end if tool == Tool.NUMBER_ARROW else rect.bottomRight()),
                color=QColor(self._color),
                pen_width=self._pen_width,
                text=str(value),
                font_family=self._font_family,
                font_point_size=self._font_point_size,
                opacity=self._opacity,
                bold=True,
                italic=False,
                underline=self._underline,
                fill_mode=self._fill_mode if tool == Tool.NUMBER_ARROW else FillMode.BORDER_AND_FILL,
                text_color=QColor(self._text_color),
                shadow=self._shadow,
            )
        return None

    def _next_number_value(self) -> int:
        value = self._number_seed
        self._number_seed += 1
        return value

    def _text_box_size(self, item: OverlayItem) -> tuple[int, int]:
        width = max(96, len(item.text or "") * max(8, (item.font_point_size or self._font_point_size) - 2) + 24)
        height = max(34, (item.font_point_size or self._font_point_size) + 18)
        return width, height

    def _draw_shadow(self, painter: QPainter, item: OverlayItem) -> None:
        shadow = item.clone()
        shadow.start += QPoint(4, 4)
        shadow.end += QPoint(4, 4)
        shadow.shadow = False
        shadow.color = QColor(0, 0, 0, 80)
        shadow.text_color = QColor(0, 0, 0, 120)
        if shadow.fill_color is not None:
            shadow.fill_color = QColor(0, 0, 0, 50)
        painter.save()
        painter.setOpacity(min(item.opacity, 0.35))
        self._draw_item(painter, shadow, False, show_handles=False)
        painter.restore()

    def _load_sticker_image(self, sticker_path: str | None) -> QImage | None:
        if not sticker_path:
            return None
        pixmap = QIcon(sticker_path).pixmap(160, 160)
        if pixmap.isNull():
            pixmap = QPixmap(sticker_path)
        if pixmap.isNull():
            image = QImage(sticker_path)
            return image if not image.isNull() else None
        return pixmap.toImage()

    def _text_arrow_label_rect(self, item: OverlayItem) -> QRect:
        width, height = self._text_box_size(item)
        dx = item.end.x() - item.start.x()
        offset_x = 12 if dx >= 0 else -(width + 12)
        top = item.start.y() - height // 2
        return QRect(item.start.x() + offset_x, top, width, height)

    def _circle_edge_point(self, center: QPoint, radius: int, target: QPoint) -> QPoint:
        dx = target.x() - center.x()
        dy = target.y() - center.y()
        if dx == 0 and dy == 0:
            return QPoint(center.x() + radius, center.y())
        length = (dx * dx + dy * dy) ** 0.5
        return QPoint(int(center.x() + dx / length * radius), int(center.y() + dy / length * radius))

    def _draw_text_pointer(self, painter: QPainter, item: OverlayItem) -> None:
        rect = QRect(item.start, item.end).normalized()
        bubble_rect = rect.adjusted(0, 0, -max(16, rect.width() // 6), -max(16, rect.height() // 6))
        bubble_rect = bubble_rect.normalized()
        fill = item.fill_color or QColor(255, 250, 245, 235)
        painter.setBrush(fill)
        painter.drawRoundedRect(bubble_rect, 8, 8)
        tip = rect.bottomRight()
        base_center = QPoint(bubble_rect.right() - 18, bubble_rect.bottom() - 10)
        triangle = QPolygon(
            [
                QPoint(base_center.x() - 8, base_center.y() - 4),
                QPoint(base_center.x() + 8, base_center.y() + 4),
                tip,
            ]
        )
        painter.drawPolygon(triangle)
        font = QFont(item.font_family or self._font_family, item.font_point_size or self._font_point_size)
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        painter.setFont(font)
        painter.setPen(QPen(item.text_color or QColor("#111111")))
        painter.drawText(
            bubble_rect.adjusted(10, 8, -10, -8),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            item.text or "",
        )

    def _draw_text_arrow(self, painter: QPainter, item: OverlayItem) -> None:
        label_rect = self._text_arrow_label_rect(item)
        arrow_start = QPoint(label_rect.right(), label_rect.center().y()) if item.end.x() >= item.start.x() else QPoint(label_rect.left(), label_rect.center().y())
        if self._has_border(item.fill_mode):
            self._draw_arrow(painter, arrow_start, item.end, color=item.color, pen_width=item.pen_width)
        painter.setBrush(item.color if self._has_fill(item.fill_mode) else Qt.BrushStyle.NoBrush)
        if self._has_border(item.fill_mode):
            painter.drawRoundedRect(label_rect, 8, 8)
        font = QFont(item.font_family or self._font_family, item.font_point_size or self._font_point_size)
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        painter.setFont(font)
        painter.setPen(QPen(item.text_color or QColor("#111111")))
        painter.drawText(
            label_rect.adjusted(10, 4, -10, -4),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
            item.text or "",
        )

    def _draw_number_badge(self, painter: QPainter, item: OverlayItem) -> None:
        rect = QRect(item.start, item.end).normalized()
        painter.setBrush(item.color if self._has_fill(item.fill_mode) else Qt.BrushStyle.NoBrush)
        if self._has_border(item.fill_mode):
            painter.drawEllipse(rect)
        font = QFont(item.font_family or self._font_family, item.font_point_size or self._font_point_size)
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        painter.setFont(font)
        painter.setPen(QPen(item.text_color or QColor("white"), max(1, item.pen_width // 2)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text or "")

    def _draw_number_pointer(self, painter: QPainter, item: OverlayItem) -> None:
        rect = QRect(item.start, item.end).normalized()
        diameter = min(rect.width(), rect.height())
        bubble_rect = QRect(rect.left(), rect.top(), diameter, diameter)
        center = bubble_rect.center()
        tail_tip = rect.bottomRight()
        tail_base = self._circle_edge_point(center, diameter // 2 - 2, tail_tip)
        tail_left = QPoint(tail_base.x() - 5, tail_base.y() + 7)
        tail_right = QPoint(tail_base.x() + 7, tail_base.y() - 5)
        painter.setBrush(item.color if self._has_fill(item.fill_mode) else Qt.BrushStyle.NoBrush)
        if self._has_border(item.fill_mode):
            painter.drawEllipse(bubble_rect)
            triangle = QPolygon([tail_left, tail_right, tail_tip])
            painter.drawPolygon(triangle)
        font = QFont(item.font_family or self._font_family, item.font_point_size or self._font_point_size)
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        painter.setFont(font)
        painter.setPen(QPen(item.text_color or QColor("white"), max(1, item.pen_width // 2)))
        painter.drawText(bubble_rect, Qt.AlignmentFlag.AlignCenter, item.text or "")

    def _draw_number_arrow(self, painter: QPainter, item: OverlayItem) -> None:
        bubble_radius = max(14, item.font_point_size or self._font_point_size)
        bubble_rect = QRect(item.start.x() - bubble_radius, item.start.y() - bubble_radius, bubble_radius * 2, bubble_radius * 2)
        bubble_center = bubble_rect.center()
        arrow_start = self._circle_edge_point(bubble_center, bubble_radius - 2, item.end)
        painter.setBrush(item.color if self._has_fill(item.fill_mode) else Qt.BrushStyle.NoBrush)
        if self._has_border(item.fill_mode):
            painter.drawEllipse(bubble_rect)
            self._draw_arrow(painter, arrow_start, item.end, color=item.color, pen_width=item.pen_width)
        font = QFont(item.font_family or self._font_family, max(8, (item.font_point_size or self._font_point_size) - 1))
        font.setBold(item.bold)
        font.setItalic(item.italic)
        font.setUnderline(item.underline)
        painter.setFont(font)
        painter.setPen(QPen(item.text_color or QColor("white"), max(1, item.pen_width // 2)))
        painter.drawText(bubble_rect, Qt.AlignmentFlag.AlignCenter, item.text or "")

    def _apply_region_effect(self, rect: QRect, tool: Tool) -> None:
        rect = rect.intersected(self._image.rect())
        if rect.isEmpty():
            return

        region = self._image.copy(rect)
        if tool == Tool.BLUR:
            processed = self._box_blur(region, radius=max(2, self._pen_width))
        else:
            processed = self._pixelate(region, block_size=max(4, self._pen_width * 2))

        painter = QPainter(self._image)
        painter.drawImage(rect.topLeft(), processed)
        painter.end()

    def _pixelate(self, image: QImage, block_size: int) -> QImage:
        small = image.scaled(
            max(1, image.width() // block_size),
            max(1, image.height() // block_size),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        return small.scaled(
            image.width(),
            image.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )

    def _box_blur(self, image: QImage, radius: int) -> QImage:
        source = image.convertToFormat(QImage.Format.Format_ARGB32)
        result = QImage(source.size(), QImage.Format.Format_ARGB32)
        width = source.width()
        height = source.height()

        for y in range(height):
            for x in range(width):
                r = g = b = a = count = 0
                for oy in range(max(0, y - radius), min(height, y + radius + 1)):
                    for ox in range(max(0, x - radius), min(width, x + radius + 1)):
                        color = source.pixelColor(ox, oy)
                        r += color.red()
                        g += color.green()
                        b += color.blue()
                        a += color.alpha()
                        count += 1
                result.setPixelColor(x, y, QColor(r // count, g // count, b // count, a // count))
        return result
