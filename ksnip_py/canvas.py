from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from enum import Enum
from math import hypot

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QImage, QMouseEvent, QPainter, QPen, QPixmap, QPolygon, QTransform
from PyQt6.QtWidgets import QLabel, QInputDialog, QSizePolicy


class Tool(str, Enum):
    SELECT = "select"
    IMAGE = "image"
    PEN = "pen"
    LINE = "line"
    ARROW = "arrow"
    RECT = "rect"
    ELLIPSE = "ellipse"
    TEXT = "text"
    BLUR = "blur"
    PIXELATE = "pixelate"
    CROP = "crop"


class FillMode(str, Enum):
    STROKE_ONLY = "stroke_only"
    FILL_ONLY = "fill_only"
    STROKE_AND_FILL = "stroke_and_fill"


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
    fill_mode: FillMode = FillMode.STROKE_AND_FILL
    bold: bool = False
    italic: bool = False
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
            image=self.image.copy() if self.image is not None else None,
        )

    def move_by(self, delta: QPoint) -> None:
        self.start += delta
        self.end += delta

    def bounds(self) -> QRect:
        if self.kind == Tool.TEXT:
            width = max(40, len(self.text or "") * 10)
            height = max(20, (self.font_point_size or max(10, self.pen_width * 4)) + 12)
            return QRect(self.start.x(), self.start.y() - height, width, height)
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
        self._color = QColor("#d9480f")
        self._pen_width = 3
        self._font_family = QFont().family()
        self._font_point_size = 14
        self._fill_color = QColor(255, 216, 168, 120)
        self._opacity = 1.0
        self._fill_mode = FillMode.STROKE_AND_FILL
        self._bold = False
        self._italic = False
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
        self.state = CanvasState()

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
            fill_mode=FillMode(payload.get("fill_mode", FillMode.STROKE_AND_FILL.value)),
            bold=payload.get("bold", False),
            italic=payload.get("italic", False),
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

    def set_opacity(self, opacity: float) -> None:
        self._opacity = max(0.0, min(1.0, opacity))

    def set_fill_mode(self, fill_mode: FillMode) -> None:
        self._fill_mode = fill_mode

    def set_bold(self, bold: bool) -> None:
        self._bold = bool(bold)

    def set_italic(self, italic: bool) -> None:
        self._italic = bool(italic)

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
        if item is None or item.kind != Tool.TEXT:
            return None
        return item.font_family or self._font_family

    def selected_item_font_point_size(self) -> int | None:
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.TEXT:
            return None
        return item.font_point_size or self._font_point_size

    def selected_item_fill_color(self) -> QColor | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return QColor(item.fill_color) if item.fill_color is not None else None

    def selected_item_opacity(self) -> int | None:
        item = self._primary_selected_item()
        if item is None:
            return None
        return round(item.opacity * 100)

    def selected_item_fill_mode(self) -> FillMode | None:
        item = self._primary_selected_item()
        if item is None or item.kind not in (Tool.RECT, Tool.ELLIPSE):
            return None
        return item.fill_mode

    def selected_item_bold(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.TEXT:
            return None
        return item.bold

    def selected_item_italic(self) -> bool | None:
        item = self._primary_selected_item()
        if item is None or item.kind != Tool.TEXT:
            return None
        return item.italic

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
        if not self.can_undo():
            return
        self._redo_stack.append(self._make_snapshot())
        snapshot = self._undo_stack.pop()
        self._restore_snapshot(snapshot)
        self.state.dirty = True
        self.changed.emit()
        self._refresh()

    def redo(self) -> None:
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
        for item in self._items:
            self._draw_item(painter, item, selected=False)
        painter.end()
        return composed

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._refresh()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.has_image():
            return
        image_point = self._map_to_image(event.position().toPoint())
        if image_point is None:
            return

        if self._tool == Tool.SELECT:
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

        if self._tool == Tool.TEXT:
            text, accepted = QInputDialog.getText(self, "Insert text", "Text:")
            if accepted and text:
                self._push_undo_state()
                self._items.append(
                    OverlayItem(
                        kind=Tool.TEXT,
                        start=QPoint(image_point),
                        end=QPoint(image_point),
                        color=QColor(self._color),
                        pen_width=self._pen_width,
                        text=text,
                        font_family=self._font_family,
                        font_point_size=self._font_point_size,
                        opacity=self._opacity,
                        bold=self._bold,
                        italic=self._italic,
                    )
                )
                self._select_single_item(len(self._items) - 1)
                self._mark_dirty()
                self._refresh()
            return

        if self._tool in (Tool.PEN, Tool.LINE, Tool.ARROW, Tool.RECT, Tool.ELLIPSE, Tool.BLUR, Tool.PIXELATE, Tool.CROP):
            self._push_undo_state()
        self._preview_start = image_point
        self._preview_end = image_point
        self._last_point = image_point
        self._clear_selection()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
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
            return
        image_point = self._map_to_image(event.position().toPoint())
        if image_point is None:
            return

        if self._tool == Tool.PEN and self._last_point is not None:
            painter = QPainter(self._image)
            pen = QPen(self._color, self._pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self._last_point, image_point)
            painter.end()
            self._last_point = image_point
            self._mark_dirty()

        self._preview_end = image_point
        self._refresh()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if not self.has_image() or self._preview_start is None:
            return

        image_point = self._map_to_image(event.position().toPoint())
        if image_point is not None:
            self._preview_end = image_point

        if self._tool in (Tool.LINE, Tool.ARROW, Tool.RECT, Tool.ELLIPSE, Tool.BLUR, Tool.PIXELATE, Tool.CROP) and self._preview_end is not None:
            rect = QRect(self._preview_start, self._preview_end).normalized()
            if self._tool in (Tool.LINE, Tool.ARROW, Tool.RECT, Tool.ELLIPSE):
                self._items.append(
                    OverlayItem(
                        kind=self._tool,
                        start=QPoint(self._preview_start),
                        end=QPoint(self._preview_end),
                        color=QColor(self._color),
                        pen_width=self._pen_width,
                        fill_color=QColor(self._fill_color) if self._tool in (Tool.RECT, Tool.ELLIPSE) else None,
                        opacity=self._opacity,
                        fill_mode=self._fill_mode,
                    )
                )
                self._select_single_item(len(self._items) - 1)
            elif self._tool == Tool.CROP:
                self._image = self._image.copy(rect)
                self._clear_selection()
            else:
                self._apply_region_effect(rect, self._tool)
                self._clear_selection()
            self._mark_dirty()

        self._preview_start = None
        self._preview_end = None
        self._last_point = None
        self._drag_start = None
        self._active_handle = None
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
        for index, item in enumerate(self._items):
            self._draw_item_preview(painter, item, sx, sy, selected=index in self._selected_item_indices, show_handles=index == self._primary_selected_index() and self.has_single_selected_item())

        if self._tool in (Tool.LINE, Tool.ARROW, Tool.RECT, Tool.ELLIPSE, Tool.BLUR, Tool.PIXELATE, Tool.CROP) and self._preview_start is not None and self._preview_end is not None:
            pen = QPen(self._color, max(1, self._pen_width))
            painter.setPen(pen)
            start_point, end_point = self._display_points()
            rect = QRect(start_point, end_point).normalized()
            if self._tool == Tool.LINE:
                painter.drawLine(start_point, end_point)
            elif self._tool == Tool.ARROW:
                self._draw_arrow(painter, start_point, end_point)
            elif self._tool in (Tool.RECT, Tool.CROP, Tool.BLUR, Tool.PIXELATE):
                painter.drawRect(rect)
            elif self._tool == Tool.ELLIPSE:
                painter.drawEllipse(rect)
            if self._tool in (Tool.BLUR, Tool.PIXELATE, Tool.CROP):
                painter.fillRect(rect, QColor(255, 255, 255, 40))
        painter.end()

        self.setPixmap(display)
        self.resize(display.size())

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
            elif item.kind == Tool.ARROW:
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
        painter.save()
        painter.setOpacity(item.opacity)
        pen_color = item.color if item.fill_mode != FillMode.FILL_ONLY else QColor(item.color.red(), item.color.green(), item.color.blue(), 0)
        pen = QPen(pen_color, item.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        if item.kind == Tool.LINE:
            painter.drawLine(item.start, item.end)
        elif item.kind == Tool.ARROW:
            self._draw_arrow(painter, item.start, item.end, color=item.color, pen_width=item.pen_width)
        elif item.kind == Tool.RECT:
            painter.setBrush(self._brush_for_item(item))
            painter.drawRect(QRect(item.start, item.end).normalized())
        elif item.kind == Tool.ELLIPSE:
            painter.setBrush(self._brush_for_item(item))
            painter.drawEllipse(QRect(item.start, item.end).normalized())
        elif item.kind == Tool.TEXT:
            font = QFont()
            if item.font_family:
                font.setFamily(item.font_family)
            font.setPointSize(item.font_point_size or max(10, item.pen_width * 4))
            font.setBold(item.bold)
            font.setItalic(item.italic)
            painter.setFont(font)
            painter.drawText(item.start, item.text or "")
        elif item.kind == Tool.IMAGE and item.image is not None and not item.image.isNull():
            painter.drawImage(QRect(item.start, item.end).normalized(), item.image)
        painter.restore()

        if selected:
            selection_pen = QPen(QColor("#1c7ed6"), 1, Qt.PenStyle.DashLine)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(item.bounds())
            if show_handles:
                painter.setBrush(QColor("#1c7ed6"))
                for handle_point in self._handle_points(item).values():
                    painter.drawRect(QRect(handle_point.x() - 3, handle_point.y() - 3, 6, 6))

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
        text, accepted = QInputDialog.getText(parent or self, "Edit text", "Text:", text=item.text or "")
        if not accepted or text == item.text:
            return False
        self._push_undo_state()
        item.text = text
        self._mark_dirty()
        self._refresh()
        return True

    def apply_font_family_to_selected_text(self, family: str) -> bool:
        item = self._primary_selected_item()
        if not self.has_single_selected_item() or item is None or item.kind != Tool.TEXT:
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
        if not self.has_single_selected_item() or item is None or item.kind != Tool.TEXT:
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
        shape_indices = [index for index in self._selected_item_indices if self._items[index].kind in (Tool.RECT, Tool.ELLIPSE)]
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
        shape_indices = [index for index in self._selected_item_indices if self._items[index].kind in (Tool.RECT, Tool.ELLIPSE)]
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
        text_indices = [index for index in self._selected_item_indices if self._items[index].kind == Tool.TEXT]
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
        text_indices = [index for index in self._selected_item_indices if self._items[index].kind == Tool.TEXT]
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

    def _brush_for_item(self, item: OverlayItem):
        if item.fill_mode == FillMode.STROKE_ONLY or item.fill_color is None:
            return Qt.BrushStyle.NoBrush
        return item.fill_color

    def _find_handle_at(self, item: OverlayItem, point: QPoint) -> str | None:
        for handle_name, handle_point in self._handle_points(item).items():
            if QRect(handle_point.x() - 6, handle_point.y() - 6, 12, 12).contains(point):
                return handle_name
        return None

    def _handle_points(self, item: OverlayItem) -> dict[str, QPoint]:
        if item.kind in (Tool.LINE, Tool.ARROW):
            return {
                "start": QPoint(item.start),
                "end": QPoint(item.end),
            }

        if item.kind in (Tool.RECT, Tool.ELLIPSE):
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
        return {
            "top_left": bounds.topLeft(),
            "top_right": bounds.topRight(),
            "bottom_left": bounds.bottomLeft(),
            "bottom_right": bounds.bottomRight(),
        }

    def _resize_item(self, item: OverlayItem, handle: str, point: QPoint) -> None:
        if item.kind in (Tool.LINE, Tool.ARROW):
            if handle == "start":
                item.start = QPoint(point)
            elif handle == "end":
                item.end = QPoint(point)
            return

        if item.kind == Tool.TEXT:
            bounds = item.bounds()
            if handle == "top_left":
                item.start = QPoint(point.x(), bounds.bottom())
            elif handle == "top_right":
                item.start = QPoint(item.start.x(), bounds.bottom())
                item.end = QPoint(point)
            elif handle == "bottom_left":
                item.start = QPoint(point.x(), point.y())
            elif handle == "bottom_right":
                item.end = QPoint(point)
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
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        if dx == 0 and dy == 0:
            return

        length = (dx * dx + dy * dy) ** 0.5
        ux = dx / length
        uy = dy / length
        resolved_pen_width = self._pen_width if pen_width is None else pen_width
        arrow_size = max(10, resolved_pen_width * 4)
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
