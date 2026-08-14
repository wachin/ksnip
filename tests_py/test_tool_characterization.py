from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, FillMode, OverlayItem, Tool
from ksnip_py.project_io import export_svg


APP = QApplication.instance() or QApplication([])


def background(width: int = 240, height: int = 160) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    return image


def embedded_image() -> QImage:
    image = QImage(18, 12, QImage.Format.Format_ARGB32)
    image.fill(QColor("magenta"))
    return image


def representative_item(tool: Tool) -> OverlayItem:
    kwargs = {
        "kind": tool,
        "start": QPoint(25, 30),
        "end": QPoint(150, 105),
        "color": QColor("#d9480f"),
        "pen_width": 5,
        "opacity": 0.72,
        "shadow": True,
        "fill_mode": FillMode.BORDER_AND_FILL,
    }
    if tool in {Tool.PEN, Tool.MARKER_PEN}:
        kwargs["points"] = [QPoint(25, 30), QPoint(60, 75), QPoint(150, 105)]
    if tool in {
        Tool.TEXT,
        Tool.TEXT_POINTER,
        Tool.TEXT_ARROW,
        Tool.NUMBER,
        Tool.NUMBER_POINTER,
        Tool.NUMBER_ARROW,
    }:
        kwargs.update(
            text="7" if tool in {Tool.NUMBER, Tool.NUMBER_POINTER, Tool.NUMBER_ARROW} else "Protected\ntext",
            font_family="Sans",
            font_point_size=19,
            bold=True,
            italic=True,
            underline=True,
            text_color=QColor("#f8f9fa"),
        )
    if tool == Tool.NUMBER_ARROW:
        kwargs["arrow_head_size"] = 31
    if tool in {Tool.IMAGE, Tool.STICKER, Tool.DUPLICATE}:
        kwargs.update(image=embedded_image(), scaling=1.25)
    if tool == Tool.STICKER:
        kwargs["sticker_path"] = "/characterization/protected-sticker.svg"
    if tool in {Tool.RECT, Tool.ELLIPSE}:
        kwargs["fill_color"] = QColor("#74c0fc")
    return OverlayItem(**kwargs)


OVERLAY_TOOLS = (
    Tool.PEN,
    Tool.MARKER_PEN,
    Tool.MARKER_RECT,
    Tool.MARKER_ELLIPSE,
    Tool.LINE,
    Tool.ARROW,
    Tool.DOUBLE_ARROW,
    Tool.RECT,
    Tool.ELLIPSE,
    Tool.NUMBER,
    Tool.NUMBER_POINTER,
    Tool.NUMBER_ARROW,
    Tool.TEXT,
    Tool.TEXT_POINTER,
    Tool.TEXT_ARROW,
    Tool.IMAGE,
    Tool.STICKER,
    Tool.DUPLICATE,
)


class ToolCharacterizationTest(unittest.TestCase):
    def test_every_selectable_tool_round_trips_all_current_project_fields(self) -> None:
        for tool in OVERLAY_TOOLS:
            with self.subTest(tool=tool.value):
                item = representative_item(tool)
                payload = AnnotationCanvas._serialize_item(item)
                restored = AnnotationCanvas._deserialize_item(payload)

                self.assertEqual(restored.kind, tool)
                self.assertEqual(restored.start, item.start)
                self.assertEqual(restored.end, item.end)
                self.assertEqual(restored.color, item.color)
                self.assertEqual(restored.pen_width, item.pen_width)
                self.assertEqual(restored.arrow_head_size, item.arrow_head_size)
                self.assertEqual(restored.text, item.text)
                self.assertEqual(restored.font_family, item.font_family)
                self.assertEqual(restored.font_point_size, item.font_point_size)
                self.assertEqual(restored.fill_color, item.fill_color)
                self.assertAlmostEqual(restored.opacity, item.opacity)
                self.assertEqual(restored.fill_mode, item.fill_mode)
                self.assertEqual(restored.bold, item.bold)
                self.assertEqual(restored.italic, item.italic)
                self.assertEqual(restored.underline, item.underline)
                self.assertEqual(restored.text_color, item.text_color)
                self.assertEqual(restored.shadow, item.shadow)
                self.assertAlmostEqual(restored.scaling, item.scaling)
                self.assertEqual(restored.sticker_path, item.sticker_path)
                self.assertEqual(restored.points, item.points)
                if item.image is not None:
                    self.assertIsNotNone(restored.image)
                    self.assertEqual(restored.image.size(), item.image.size())

    def test_every_selectable_tool_renders_without_mutating_its_metadata(self) -> None:
        for tool in OVERLAY_TOOLS:
            with self.subTest(tool=tool.value):
                canvas = AnnotationCanvas()
                canvas.set_image(background())
                item = representative_item(tool)
                before = AnnotationCanvas._serialize_item(item)
                canvas._items = [item]

                rendered = canvas.image()

                self.assertFalse(rendered.isNull())
                self.assertEqual(rendered.size(), canvas.background_image().size())
                self.assertEqual(AnnotationCanvas._serialize_item(item), before)

    def test_current_drag_factories_preserve_basic_tool_defaults(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(background())
        canvas.set_color(QColor("#228be6"))
        canvas.set_pen_width(7)
        canvas.set_shadow(True)
        start = QPoint(30, 40)
        end = QPoint(170, 110)
        rect = QRect(start, end).normalized()

        canvas._preview_points = [start, QPoint(80, 65), end]
        tools = (
            Tool.PEN,
            Tool.MARKER_PEN,
            Tool.LINE,
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.DUPLICATE,
        )
        for tool in tools:
            with self.subTest(tool=tool.value):
                item = canvas._build_drag_item(tool, start, end, rect)
                self.assertIsNotNone(item)
                self.assertEqual(item.kind, tool)

        marker_pen = canvas._build_drag_item(Tool.MARKER_PEN, start, end, rect)
        self.assertEqual(marker_pen.color.alpha(), 110)
        self.assertFalse(marker_pen.shadow)
        for tool in (Tool.MARKER_RECT, Tool.MARKER_ELLIPSE):
            marker = canvas._build_drag_item(tool, start, end, rect)
            self.assertEqual(marker.fill_mode, FillMode.NO_BORDER_AND_FILL)
            self.assertEqual(marker.pen_width, 1)
            self.assertFalse(marker.shadow)

    def test_number_and_sticker_click_factories_preserve_centering_and_defaults(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(background())
        click = QPoint(90, 70)

        number = canvas._build_click_item(Tool.NUMBER, click)
        self.assertIsNotNone(number)
        self.assertEqual(number.kind, Tool.NUMBER)
        self.assertEqual(number.text, "1")
        self.assertEqual(number.bounds().center(), click)

        sticker_path = Path(__file__).resolve().parents[1] / "ksnip_py" / "stickers" / "tutorial_attention.svg"
        canvas.set_sticker_path(str(sticker_path))
        sticker = canvas._build_click_item(Tool.STICKER, click)
        self.assertIsNotNone(sticker)
        self.assertEqual(sticker.kind, Tool.STICKER)
        # QRect uses inclusive bottom/right coordinates. Even-sized stickers
        # therefore retain the current, protected one-pixel centering tolerance.
        self.assertLessEqual(abs(sticker.bounds().center().x() - click.x()), 1)
        self.assertLessEqual(abs(sticker.bounds().center().y() - click.y()), 1)
        self.assertLessEqual(max(sticker.bounds().width(), sticker.bounds().height()), 51)

    def test_blur_and_pixelate_remain_undoable_background_operations(self) -> None:
        source = background(80, 60)
        for y in range(15, 45):
            for x in range(20, 60):
                source.setPixelColor(x, y, QColor((x * 9) % 255, (y * 11) % 255, 100))

        for tool in (Tool.BLUR, Tool.PIXELATE):
            with self.subTest(tool=tool.value):
                canvas = AnnotationCanvas()
                canvas.set_image(source)
                canvas._push_undo_state()
                before = canvas.background_image()

                canvas._apply_region_effect(QRect(20, 15, 40, 30), tool)

                self.assertNotEqual(canvas.background_image(), before)
                self.assertEqual(canvas._items, [])
                canvas.undo()
                self.assertEqual(canvas.background_image(), before)

    def test_svg_export_keeps_each_current_overlay_category(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(background())
        canvas._items = [representative_item(tool) for tool in OVERLAY_TOOLS]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "all-tools.svg"
            export_svg(str(path), canvas)
            svg = path.read_text(encoding="utf-8")

        self.assertIn("<polyline", svg)
        self.assertIn("<line", svg)
        self.assertIn("<rect", svg)
        self.assertIn("<ellipse", svg)
        self.assertIn("<text", svg)
        self.assertIn("marker-start=", svg)
        self.assertIn("marker-end=", svg)
        self.assertGreaterEqual(svg.count("<image"), 4)  # background + Image/Sticker/Duplicate


if __name__ == "__main__":
    unittest.main()
