import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtTest import QTest

from ksnip_py.canvas import AnnotationCanvas, CutDialog, FillMode, ModifyCanvasDialog, OverlayItem, RotateDialog, ScaleDialog, Tool


APP = QApplication.instance() or QApplication([])


def coordinate_image(width: int = 10, height: int = 8) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    for y in range(height):
        for x in range(width):
            image.setPixelColor(x, y, QColor((x * 20) % 256, (y * 20) % 256, 0))
    return image


class CropAndCutParityTest(unittest.TestCase):
    def test_crop_moves_overlays_and_undo_restores_them(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image())
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas.add_image_item(overlay, QPoint(6, 5))
        canvas._push_undo_state()

        self.assertTrue(canvas._crop_to_rect(QRect(3, 2, 6, 5)))
        self.assertEqual(canvas._items[0].start, QPoint(3, 3))
        canvas.undo()
        self.assertEqual(canvas._items[0].start, QPoint(6, 5))

    def test_cut_removes_a_full_axis_slice(self) -> None:
        source = coordinate_image()
        canvas = AnnotationCanvas()
        canvas.set_image(source)

        self.assertTrue(canvas.cut_slice(QRect(3, 2, 2, 2)))
        self.assertEqual(canvas._image.size(), QImage(8, 8, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(3, 4), source.pixelColor(5, 4))
        canvas.undo()
        self.assertEqual(canvas._image.size(), source.size())

    def test_cut_dialog_uses_explicit_orientation(self) -> None:
        dialog = CutDialog(coordinate_image(300, 180))
        self.assertEqual(dialog.cut_rect(), QRect(100, 0, 100, 180))
        dialog.horizontal.setChecked(True)
        self.assertEqual(dialog.cut_rect(), QRect(0, 40, 300, 100))


class DuplicateToolParityTest(unittest.TestCase):
    def test_duplicate_captures_the_composed_scene_as_a_movable_image_item(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(12, 10))
        overlay = QImage(3, 3, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas.add_image_item(overlay, QPoint(2, 2))

        rect = QRect(1, 1, 6, 5)
        duplicate = canvas._build_drag_item(Tool.DUPLICATE, rect.topLeft(), rect.bottomRight(), rect)

        self.assertIsNotNone(duplicate)
        self.assertEqual(duplicate.kind, Tool.DUPLICATE)
        self.assertEqual(duplicate.image.size(), rect.size())
        self.assertEqual(duplicate.image.pixelColor(1, 1), QColor("red"))
        self.assertFalse(duplicate.shadow)

    def test_duplicate_is_restored_by_undo(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(12, 10))
        rect = QRect(1, 1, 5, 4)
        canvas._push_undo_state()
        canvas._items.append(canvas._build_drag_item(Tool.DUPLICATE, rect.topLeft(), rect.bottomRight(), rect))
        self.assertEqual(len(canvas._items), 1)
        canvas.undo()
        self.assertEqual(canvas._items, [])


class ItemShadowParityTest(unittest.TestCase):
    def test_new_line_and_shape_items_keep_the_selected_shadow_setting(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(40, 30))
        rect = QRect(5, 5, 20, 12)
        canvas.set_shadow(True)

        for tool in (Tool.LINE, Tool.ARROW, Tool.DOUBLE_ARROW, Tool.RECT, Tool.ELLIPSE):
            item = canvas._build_drag_item(tool, rect.topLeft(), rect.bottomRight(), rect)
            self.assertTrue(item.shadow, tool)

        for tool in (Tool.MARKER_RECT, Tool.MARKER_ELLIPSE):
            item = canvas._build_drag_item(tool, rect.topLeft(), rect.bottomRight(), rect)
            self.assertFalse(item.shadow, tool)

    def test_changing_item_shadow_is_undoable(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(40, 30))
        rect = QRect(5, 5, 20, 12)
        item = canvas._build_drag_item(Tool.RECT, rect.topLeft(), rect.bottomRight(), rect)
        canvas._items.append(item)
        canvas._select_single_item(0)

        self.assertTrue(canvas.apply_shadow_to_selected_item(False))
        self.assertFalse(canvas._items[0].shadow)
        canvas.undo()
        self.assertTrue(canvas._items[0].shadow)


class FreehandToolParityTest(unittest.TestCase):
    def test_pen_creates_a_non_destructive_item_with_opacity_and_shadow(self) -> None:
        source = coordinate_image(40, 30)
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.set_opacity(0.4)
        canvas.set_shadow(True)
        canvas._preview_points = [QPoint(5, 5), QPoint(10, 8), QPoint(18, 6)]

        item = canvas._build_drag_item(Tool.PEN, QPoint(5, 5), QPoint(18, 6), QRect(5, 5, 14, 4))
        self.assertEqual(item.kind, Tool.PEN)
        self.assertEqual(item.opacity, 0.4)
        self.assertTrue(item.shadow)
        self.assertEqual(len(item.points), 3)
        canvas._items.append(item)
        self.assertEqual(canvas.background_image(), source)
        self.assertNotEqual(canvas.image(), source)

        original_points = [QPoint(point) for point in item.points]
        item.move_by(QPoint(3, 4))
        self.assertEqual(item.points, [point + QPoint(3, 4) for point in original_points])

    def test_marker_pen_remains_translucent_without_shadow_or_item_opacity(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(40, 30))
        canvas.set_pen_width(4)
        canvas.set_opacity(0.2)
        canvas.set_shadow(True)
        canvas._preview_points = [QPoint(4, 4), QPoint(20, 10)]
        item = canvas._build_drag_item(Tool.MARKER_PEN, QPoint(4, 4), QPoint(20, 10), QRect(4, 4, 17, 7))
        self.assertEqual(item.opacity, 1.0)
        self.assertFalse(item.shadow)
        self.assertEqual(item.color.alpha(), 110)
        self.assertEqual(item.pen_width, 4)

    def test_marker_pen_uses_multiply_composition_like_cpp(self) -> None:
        background = QImage(30, 20, QImage.Format.Format_ARGB32)
        background.fill(QColor(80, 140, 210))
        canvas = AnnotationCanvas()
        canvas.set_image(background)
        canvas.set_color(QColor("yellow"))
        canvas.set_pen_width(6)
        canvas._preview_points = [QPoint(4, 10), QPoint(25, 10)]
        item = canvas._build_drag_item(Tool.MARKER_PEN, QPoint(4, 10), QPoint(25, 10), QRect(4, 10, 22, 1))
        canvas._items.append(item)

        pixel = canvas.image().pixelColor(15, 10)
        source = background.pixelColor(15, 10)
        self.assertLessEqual(pixel.red(), source.red())
        self.assertLessEqual(pixel.green(), source.green())
        self.assertLess(pixel.blue(), source.blue())

    def test_marker_shapes_are_filled_without_border_or_shadow(self) -> None:
        background = QImage(40, 30, QImage.Format.Format_ARGB32)
        background.fill(QColor(80, 140, 210))
        for tool in (Tool.MARKER_RECT, Tool.MARKER_ELLIPSE):
            canvas = AnnotationCanvas()
            canvas.set_image(background)
            canvas.set_color(QColor("yellow"))
            rect = QRect(5, 5, 24, 18)
            item = canvas._build_drag_item(tool, rect.topLeft(), rect.bottomRight(), rect)
            self.assertEqual(item.fill_mode, FillMode.NO_BORDER_AND_FILL)
            self.assertFalse(item.shadow)
            self.assertEqual(item.pen_width, 1)
            canvas._items.append(item)
            center = canvas.image().pixelColor(rect.center())
            source = background.pixelColor(rect.center())
            self.assertLess(center.blue(), source.blue())

    def test_freehand_points_survive_clipboard_serialization(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(40, 30))
        canvas._preview_points = [QPoint(2, 3), QPoint(8, 9), QPoint(15, 6)]
        item = canvas._build_drag_item(Tool.PEN, QPoint(2, 3), QPoint(15, 6), QRect(2, 3, 14, 7))
        restored = canvas._deserialize_item(canvas._serialize_item(item))
        self.assertEqual(restored.points, item.points)
        self.assertEqual(restored.kind, Tool.PEN)


class NumberFontParityTest(unittest.TestCase):
    def test_update_all_number_mode_renumbers_on_seed_change_and_delete(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(260, 160))
        canvas._items = [
            OverlayItem(Tool.NUMBER, QPoint(20, 20), QPoint(50, 50), QColor("red"), 2, text="3"),
            OverlayItem(Tool.NUMBER_POINTER, QPoint(80, 20), QPoint(130, 60), QColor("red"), 1, text="4"),
            OverlayItem(Tool.NUMBER_ARROW, QPoint(170, 50), QPoint(230, 50), QColor("red"), 2, text="5"),
        ]
        canvas.set_number_seed_updates_all(True)

        canvas.set_number_seed(10)
        self.assertEqual([item.text for item in canvas._items], ["10", "11", "12"])
        self.assertTrue(canvas.can_undo())
        canvas._select_single_item(1)
        self.assertTrue(canvas.delete_selected_item())
        self.assertEqual([item.text for item in canvas._items], ["10", "11"])
        self.assertEqual(canvas._next_number_value(), 12)

    def test_update_all_mode_normalizes_existing_values_when_adding_a_clone(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(260, 160))
        canvas.set_number_seed(10)
        canvas.set_number_seed_updates_all(True)
        canvas._items = [
            OverlayItem(Tool.NUMBER, QPoint(20, 20), QPoint(50, 50), QColor("red"), 2, text="99"),
            OverlayItem(Tool.NUMBER_POINTER, QPoint(80, 20), QPoint(130, 60), QColor("red"), 1, text="42"),
        ]
        canvas._select_single_item(0)

        self.assertTrue(canvas.duplicate_selected_item())
        self.assertEqual([item.text for item in canvas._items], ["10", "11", "12"])
        canvas.undo()
        self.assertEqual([item.text for item in canvas._items], ["99", "42"])


class AnnotatorBehaviorParityTest(unittest.TestCase):
    def test_switch_to_select_request_is_emitted_only_when_enabled(self) -> None:
        canvas = AnnotationCanvas()
        requests: list[bool] = []
        canvas.select_tool_requested.connect(lambda: requests.append(True))

        canvas._request_select_tool_after_drawing()
        self.assertEqual(requests, [])
        canvas.set_switch_to_select_after_drawing(True)
        canvas._request_select_tool_after_drawing()
        self.assertEqual(requests, [True])

    def test_select_item_after_drawing_can_clear_selection_but_duplicate_keeps_it(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_switch_to_select_after_drawing(True)
        canvas.set_select_item_after_drawing(False)
        normal = OverlayItem(Tool.RECT, QPoint(10, 10), QPoint(40, 40), QColor("red"), 2)
        duplicate = OverlayItem(Tool.DUPLICATE, QPoint(50, 10), QPoint(80, 40), QColor("red"), 1)
        canvas._items = [normal, duplicate]

        canvas._select_single_item(0)
        canvas._request_select_tool_after_drawing(normal)
        self.assertFalse(canvas.has_selected_item())
        canvas._select_single_item(1)
        canvas._request_select_tool_after_drawing(duplicate)
        self.assertEqual(canvas.selected_item_kind(), Tool.DUPLICATE)

    def test_duplicated_number_variants_receive_new_sequential_values(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(260, 160))
        canvas.set_number_seed(7)
        canvas._items = [
            OverlayItem(Tool.NUMBER, QPoint(20, 20), QPoint(50, 50), QColor("red"), 2, text="1"),
            OverlayItem(Tool.NUMBER_POINTER, QPoint(80, 20), QPoint(130, 60), QColor("red"), 1, text="2"),
            OverlayItem(Tool.NUMBER_ARROW, QPoint(170, 50), QPoint(230, 50), QColor("red"), 2, text="3"),
        ]
        canvas._selected_item_indices = [0, 1, 2]
        canvas._primary_selected_item_index = 2

        self.assertTrue(canvas.duplicate_selected_item())
        self.assertEqual([item.text for item in canvas._items[3:]], ["7", "8", "9"])
        self.assertEqual(canvas.number_seed(), 10)
        duplicated_badge = canvas._items[3]
        self.assertEqual(QRect(duplicated_badge.start, duplicated_badge.end).normalized().width(), duplicated_badge.number_badge_diameter())

        canvas.undo()
        self.assertEqual(len(canvas._items), 3)
        self.assertEqual(canvas.number_seed(), 10)

    def test_number_creation_and_value_changes_recalculate_the_badge(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(240, 140))
        canvas.set_font_point_size(20)
        canvas.set_bold(True)
        item = canvas._build_click_item(Tool.NUMBER, QPoint(100, 70))
        self.assertIsNotNone(item)
        initial_rect = QRect(item.start, item.end).normalized()
        self.assertEqual(initial_rect.center(), QPoint(100, 70))
        self.assertEqual(initial_rect.width(), item.number_badge_diameter())
        canvas._items = [item]
        canvas._select_single_item(0)

        self.assertTrue(canvas.apply_number_to_selected_item(100))
        changed_rect = QRect(item.start, item.end).normalized()
        self.assertEqual(changed_rect.center(), initial_rect.center())
        self.assertGreater(changed_rect.width(), initial_rect.width())
        self.assertEqual(changed_rect.width(), item.number_badge_diameter())

        canvas.undo()
        restored = canvas._items[0]
        self.assertEqual(restored.text, "1")
        self.assertEqual(QRect(restored.start, restored.end).normalized(), initial_rect)

    def test_number_badge_resizes_around_its_center_when_font_changes(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(200, 120))
        item = OverlayItem(
            kind=Tool.NUMBER, start=QPoint(40, 40), end=QPoint(70, 70),
            color=QColor("red"), pen_width=2, text="88", font_point_size=12,
        )
        canvas._items = [item]
        canvas._select_single_item(0)
        original_rect = QRect(item.start, item.end).normalized()

        self.assertTrue(canvas.apply_font_point_size_to_selected_text(36))
        resized_rect = QRect(item.start, item.end).normalized()
        self.assertEqual(resized_rect.center(), original_rect.center())
        self.assertGreater(resized_rect.width(), original_rect.width())
        self.assertEqual(resized_rect.width(), resized_rect.height())

        canvas.undo()
        restored_rect = QRect(canvas._items[0].start, canvas._items[0].end).normalized()
        self.assertEqual(restored_rect, original_rect)

    def test_number_pointer_and_arrow_bounds_follow_the_font_metrics(self) -> None:
        pointer = OverlayItem(
            kind=Tool.NUMBER_POINTER, start=QPoint(20, 20), end=QPoint(50, 30),
            color=QColor("red"), pen_width=1, text="88", font_point_size=12,
        )
        arrow = OverlayItem(
            kind=Tool.NUMBER_ARROW, start=QPoint(70, 70), end=QPoint(180, 70),
            color=QColor("red"), pen_width=2, text="88", font_point_size=12,
        )
        small_pointer_width = pointer.bounds().width()
        small_arrow_height = arrow.bounds().height()
        pointer.font_point_size = 36
        arrow.font_point_size = 36

        self.assertGreater(pointer.number_badge_diameter(), 40)
        self.assertGreater(pointer.bounds().width(), small_pointer_width)
        self.assertGreater(arrow.bounds().height(), small_arrow_height)
        self.assertTrue(pointer.bounds().contains(pointer.start))
        self.assertTrue(arrow.bounds().contains(arrow.start))

    def test_number_pointer_handles_and_hit_testing_follow_visible_geometry(self) -> None:
        canvas = AnnotationCanvas()
        item = OverlayItem(
            kind=Tool.NUMBER_POINTER, start=QPoint(20, 20), end=QPoint(180, 100),
            color=QColor("red"), pen_width=1, text="1", font_point_size=20,
        )
        canvas._items = [item]
        bubble = item.number_pointer_bubble_rect()

        self.assertEqual(canvas._handle_points(item), {"start": bubble.center(), "end": item.end})
        self.assertEqual(canvas._find_item_at(bubble.center()), 0)
        self.assertEqual(canvas._find_item_at(item.end), 0)
        self.assertIsNone(canvas._find_item_at(QPoint(bubble.right() + 5, bubble.bottom() + 35)))

        original_tip = QPoint(item.end)
        canvas._resize_item(item, "start", QPoint(80, 60))
        self.assertEqual(item.number_pointer_bubble_rect().center(), QPoint(80, 60))
        self.assertEqual(item.end, original_tip)
        canvas._resize_item(item, "end", QPoint(190, 30))
        self.assertEqual(item.end, QPoint(190, 30))

    def test_number_tools_use_the_configured_font_styles(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_bold(False)
        canvas.set_italic(True)
        canvas.set_underline(True)

        number = canvas._build_click_item(Tool.NUMBER, QPoint(40, 40))
        rect = QRect(QPoint(10, 10), QPoint(60, 50)).normalized()
        number_pointer = canvas._build_drag_item(Tool.NUMBER_POINTER, QPoint(10, 10), QPoint(60, 50), rect)
        number_arrow = canvas._build_drag_item(Tool.NUMBER_ARROW, QPoint(10, 10), QPoint(60, 50), rect)

        for item in (number, number_pointer, number_arrow):
            self.assertIsNotNone(item)
            self.assertFalse(item.bold)
            self.assertTrue(item.italic)
            self.assertTrue(item.underline)

    def test_text_and_number_arrows_remain_visible_without_label_border(self) -> None:
        canvas = AnnotationCanvas()
        image = QImage(200, 100, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        text_arrow = OverlayItem(
            kind=Tool.TEXT_ARROW, start=QPoint(20, 50), end=QPoint(170, 50),
            color=QColor("red"), pen_width=2, text="Text", fill_mode=FillMode.NO_BORDER_AND_NO_FILL,
        )
        number_arrow = OverlayItem(
            kind=Tool.NUMBER_ARROW, start=QPoint(40, 50), end=QPoint(170, 50),
            color=QColor("red"), pen_width=2, text="1", fill_mode=FillMode.NO_BORDER_AND_NO_FILL,
        )
        try:
            with patch.object(canvas, "_draw_arrow") as draw_arrow:
                canvas._draw_text_arrow(painter, text_arrow)
                canvas._draw_number_arrow(painter, number_arrow)
                self.assertEqual(draw_arrow.call_count, 2)
        finally:
            painter.end()

    def test_text_and_number_arrows_can_be_selected_from_their_labels(self) -> None:
        canvas = AnnotationCanvas()
        text_arrow = OverlayItem(
            kind=Tool.TEXT_ARROW, start=QPoint(30, 50), end=QPoint(180, 50),
            color=QColor("red"), pen_width=2, text="Text",
            font_point_size=15, fill_mode=FillMode.NO_BORDER_AND_NO_FILL,
        )
        number_arrow = OverlayItem(
            kind=Tool.NUMBER_ARROW, start=QPoint(50, 120), end=QPoint(180, 120),
            color=QColor("red"), pen_width=2, text="1",
            font_point_size=20, fill_mode=FillMode.NO_BORDER_AND_NO_FILL,
        )
        canvas._items = [text_arrow, number_arrow]

        self.assertEqual(canvas._find_item_at(canvas._text_arrow_label_rect(text_arrow).center()), 0)
        self.assertEqual(canvas._find_item_at(number_arrow.start), 1)
        self.assertIsNone(canvas._find_item_at(QPoint(10, 10)))

    def test_left_text_arrow_bounds_contain_the_rendered_multiline_label(self) -> None:
        canvas = AnnotationCanvas()
        item = OverlayItem(
            kind=Tool.TEXT_ARROW, start=QPoint(180, 60), end=QPoint(20, 60),
            color=QColor("red"), pen_width=2, text="First line\nSecond line",
            font_point_size=18, italic=True,
        )
        label_rect = canvas._text_arrow_label_rect(item)

        self.assertLess(label_rect.right(), item.start.x())
        self.assertTrue(item.bounds().contains(label_rect))
        self.assertGreater(label_rect.height(), 34)


class TextVariantEditingParityTest(unittest.TestCase):
    def test_text_pointer_handles_hit_testing_and_bounds_follow_visible_geometry(self) -> None:
        canvas = AnnotationCanvas()
        item = OverlayItem(
            kind=Tool.TEXT_POINTER, start=QPoint(100, 60), end=QPoint(20, 20),
            color=QColor("red"), pen_width=2, text="Pointer text", font_point_size=16,
        )
        canvas._items = [item]
        bubble = item.text_pointer_bubble_rect()

        self.assertEqual(canvas._handle_points(item), {"start": bubble.center(), "end": item.end})
        self.assertEqual(canvas._find_item_at(bubble.center()), 0)
        self.assertEqual(canvas._find_item_at(item.end), 0)
        self.assertTrue(item.bounds().contains(bubble))
        self.assertIsNone(canvas._find_item_at(QPoint(bubble.right() + 30, bubble.bottom() + 30)))

        original_tip = QPoint(item.end)
        canvas._resize_item(item, "start", QPoint(160, 90))
        self.assertEqual(item.text_pointer_bubble_rect().center(), QPoint(160, 90))
        self.assertEqual(item.end, original_tip)
        canvas._resize_item(item, "end", QPoint(250, 120))
        self.assertEqual(item.end, QPoint(250, 120))

    def test_text_pointer_uses_its_tool_color_as_fill(self) -> None:
        canvas = AnnotationCanvas()
        item = OverlayItem(
            kind=Tool.TEXT_POINTER, start=QPoint(20, 20), end=QPoint(160, 80),
            color=QColor("#d92727"), pen_width=2, text="Pointer",
            fill_color=QColor("white"), fill_mode=FillMode.BORDER_AND_FILL,
        )
        painter = MagicMock()

        canvas._draw_text_pointer(painter, item)

        painter.setBrush.assert_called_once_with(item.color)

    def test_text_pointer_and_text_arrow_can_be_reedited_and_undone(self) -> None:
        class AcceptedTextDialog:
            def __init__(self, parent=None, *, title: str, text: str = "") -> None:
                self.original_text = text

            def exec(self):
                return QDialog.DialogCode.Accepted

            def text(self) -> str:
                return "Updated text"

        for tool in (Tool.TEXT_POINTER, Tool.TEXT_ARROW):
            with self.subTest(tool=tool):
                canvas = AnnotationCanvas()
                canvas.set_image(coordinate_image(200, 120))
                item = OverlayItem(
                    kind=tool, start=QPoint(20, 20), end=QPoint(160, 80),
                    color=QColor("red"), pen_width=2, text="Original text",
                )
                canvas._items = [item]
                canvas._select_single_item(0)
                with patch("ksnip_py.canvas.TextInputDialog", AcceptedTextDialog):
                    self.assertTrue(canvas.edit_selected_text())
                self.assertEqual(item.text, "Updated text")
                self.assertTrue(canvas.can_undo())
                canvas.undo()
                self.assertEqual(canvas._items[0].text, "Original text")


class ImageEffectParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image = QImage(20, 12, QImage.Format.Format_ARGB32)
        self.image.fill(QColor("white"))
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(self.image)

    def test_effects_are_exclusive_and_non_destructive(self) -> None:
        self.assertTrue(self.canvas.set_image_effect("invert"))
        self.assertEqual(self.canvas.image().pixelColor(0, 0), QColor("black"))
        self.assertEqual(self.canvas.background_image().pixelColor(0, 0), QColor("white"))
        self.assertTrue(self.canvas.set_image_effect("none"))
        self.assertEqual(self.canvas.image().pixelColor(0, 0), QColor("white"))

    def test_drop_shadow_adds_margin_without_changing_background(self) -> None:
        self.canvas.set_image_effect("drop_shadow")
        rendered = self.canvas.image()
        self.assertEqual(rendered.size(), QImage(80, 74, QImage.Format.Format_ARGB32).size())
        self.assertEqual(self.canvas.background_image().size(), self.image.size())
        self.canvas._refresh()
        self.assertEqual(self.canvas._map_to_image(QPoint(30, 30)), QPoint(0, 0))
        self.assertIsNone(self.canvas._map_to_image(QPoint(10, 10)))


class RotateAndFlipParityTest(unittest.TestCase):
    def test_rotate_dialog_exposes_original_operations(self) -> None:
        dialog = RotateDialog()
        self.assertEqual(dialog.operation(), ("rotate", 180))
        dialog.rotate_clockwise.setChecked(True)
        self.assertEqual(dialog.operation(), ("rotate", 90))
        dialog.rotate_counterclockwise.setChecked(True)
        self.assertEqual(dialog.operation(), ("rotate", -90))
        dialog.rotate_arbitrary.setChecked(True)
        dialog.arbitrary_angle.setValue(37)
        self.assertEqual(dialog.operation(), ("rotate", 37))
        dialog.flip_horizontal.setChecked(True)
        self.assertEqual(dialog.operation(), ("flip", "horizontal"))
        dialog.flip_vertical.setChecked(True)
        self.assertEqual(dialog.operation(), ("flip", "vertical"))

    def test_horizontal_flip_changes_background_only_and_supports_undo(self) -> None:
        source = coordinate_image(4, 3)
        overlay = QImage(1, 1, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(1, 1))

        self.assertTrue(canvas.flip_image("horizontal"))
        self.assertEqual(canvas._image.pixelColor(0, 1), source.pixelColor(3, 1))
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))

    def test_rotation_changes_background_only_and_supports_undo(self) -> None:
        source = coordinate_image(4, 3)
        overlay = QImage(1, 1, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(1, 1))

        self.assertTrue(canvas.rotate(90))
        self.assertEqual((canvas._image.width(), canvas._image.height()), (3, 4))
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(1, 1))


class ScaleParityTest(unittest.TestCase):
    def test_dialog_synchronizes_pixel_and_percent_with_aspect_ratio(self) -> None:
        dialog = ScaleDialog(QImage(500, 250, QImage.Format.Format_ARGB32).size())
        dialog.width_pixel.setValue(250)
        self.assertEqual(dialog.width_percent.value(), 50)
        self.assertEqual(dialog.height_pixel.value(), 125)
        self.assertEqual(dialog.height_percent.value(), 50)

        dialog.height_percent.setValue(200)
        self.assertEqual(dialog.new_size(), QImage(1000, 500, QImage.Format.Format_ARGB32).size())

    def test_dialog_allows_non_uniform_scaling_when_aspect_is_disabled(self) -> None:
        dialog = ScaleDialog(QImage(500, 250, QImage.Format.Format_ARGB32).size())
        dialog.keep_aspect_ratio.setChecked(False)
        dialog.width_percent.setValue(50)
        dialog.height_percent.setValue(200)
        self.assertEqual(dialog.new_size(), QImage(250, 500, QImage.Format.Format_ARGB32).size())

    def test_scale_transforms_item_geometry_but_not_stroke_width(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(10, 8))
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas.add_image_item(overlay, QPoint(2, 2))
        original_width = canvas._items[0].pen_width

        self.assertTrue(canvas.scale_to_size(20, 4))
        self.assertEqual(canvas._items[0].start, QPoint(4, 1))
        self.assertEqual(canvas._items[0].end, QPoint(8, 2))
        self.assertEqual(canvas._items[0].pen_width, original_width)
        canvas.undo()
        self.assertEqual(canvas._image.size(), coordinate_image(10, 8).size())
        self.assertEqual(canvas._items[0].start, QPoint(2, 2))


class ModifyCanvasParityTest(unittest.TestCase):
    def test_restricted_dialog_keeps_the_background_inside_the_canvas(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.position_x.setValue(2)
        self.assertEqual(dialog.position_x.value(), 0)
        dialog.canvas_width.setValue(5)
        self.assertEqual(dialog.canvas_width.value(), 10)
        dialog.position_x.setValue(-3)
        self.assertEqual(dialog.canvas_width.value(), 13)

    def test_unrestricted_dialog_allows_cropping_from_any_origin(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.restricted.setChecked(False)
        dialog.position_x.setValue(2)
        dialog.position_y.setValue(1)
        dialog.canvas_width.setValue(5)
        dialog.canvas_height.setValue(4)
        self.assertEqual(dialog.canvas_rect(), QRect(2, 1, 5, 4))

    def test_preview_is_bounded_for_a_very_large_canvas(self) -> None:
        dialog = ModifyCanvasDialog(coordinate_image())
        dialog.canvas_width.setValue(32768)
        dialog.canvas_height.setValue(32768)
        self.assertLessEqual(dialog.preview.pixmap().width(), 760)
        self.assertLessEqual(dialog.preview.pixmap().height(), 480)

    def test_modify_canvas_expands_moves_items_and_supports_undo(self) -> None:
        source = coordinate_image()
        overlay = QImage(2, 2, QImage.Format.Format_ARGB32)
        overlay.fill(QColor("red"))
        canvas = AnnotationCanvas()
        canvas.set_image(source)
        canvas.add_image_item(overlay, QPoint(4, 3))

        self.assertTrue(canvas.modify_canvas_rect(QRect(-2, -1, 14, 10), QColor("magenta")))
        self.assertEqual(canvas._image.size(), QImage(14, 10, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(2, 1), source.pixelColor(0, 0))
        self.assertEqual(canvas._image.pixelColor(0, 0), QColor("magenta"))
        self.assertEqual(canvas._items[0].start, QPoint(6, 4))
        canvas.undo()
        self.assertEqual(canvas._image, source)
        self.assertEqual(canvas._items[0].start, QPoint(4, 3))

    def test_modify_canvas_can_crop_using_an_explicit_origin(self) -> None:
        source = coordinate_image()
        canvas = AnnotationCanvas()
        canvas.set_image(source)

        self.assertTrue(canvas.modify_canvas_rect(QRect(2, 1, 5, 4)))
        self.assertEqual(canvas._image.size(), QImage(5, 4, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas._image.pixelColor(0, 0), source.pixelColor(2, 1))


class ZoomParityTest(unittest.TestCase):
    def test_zoom_uses_ten_percent_steps_and_original_limits(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image())
        canvas.set_zoom_percent(795)
        canvas.zoom_in()
        self.assertEqual(canvas.zoom_percent(), 800)
        canvas.set_zoom_percent(15)
        canvas.zoom_out()
        self.assertEqual(canvas.zoom_percent(), 10)
        canvas.reset_zoom()
        self.assertEqual(canvas.zoom_percent(), 100)

    def test_fit_zoom_keeps_aspect_ratio_and_stays_in_range(self) -> None:
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(400, 200))
        canvas.fit_to_size(QImage(200, 200, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas.zoom_percent(), 50)
        canvas.fit_to_size(QImage(10000, 10000, QImage.Format.Format_ARGB32).size())
        self.assertEqual(canvas.zoom_percent(), 800)


class StickerInsertionParityTest(unittest.TestCase):
    def test_click_inserts_selected_sticker_and_undo_removes_it(self) -> None:
        sticker = Path(__file__).resolve().parents[1] / "ksnip_py" / "stickers" / "tutorial_attention.svg"
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(100, 80))
        canvas.set_sticker_path(str(sticker))
        canvas.set_tool(Tool.STICKER)

        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(50, 40))

        self.assertEqual(len(canvas._items), 1)
        self.assertEqual(canvas._items[0].kind, Tool.STICKER)
        self.assertEqual(canvas._items[0].sticker_path, str(sticker))
        self.assertFalse(canvas._items[0].image.isNull())
        self.assertEqual(max(canvas._items[0].bounds().width(), canvas._items[0].bounds().height()), 50)
        self.assertGreaterEqual(max(canvas._items[0].image.width(), canvas._items[0].image.height()), 256)
        self.assertTrue(canvas.state.dirty)
        self.assertNotEqual(canvas.image(), canvas.background_image())
        canvas.undo()
        self.assertEqual(canvas._items, [])

    def test_external_svg_and_png_stickers_can_build_click_items(self) -> None:
        themes = Path(__file__).resolve().parents[1] / "ksnip_py" / "stickers" / "themes"
        candidates = (
            themes / "papirus" / "face-smile.svg",
            themes / "gnome" / "face-smile.png",
            themes / "numix" / "face-smile.svg",
        )
        canvas = AnnotationCanvas()
        canvas.set_image(coordinate_image(100, 80))
        for sticker in candidates:
            if not sticker.is_file() or sticker.is_symlink():
                continue
            canvas.set_sticker_path(str(sticker))
            item = canvas._build_click_item(Tool.STICKER, QPoint(50, 40))
            self.assertIsNotNone(item, str(sticker))
            self.assertFalse(item.image.isNull(), str(sticker))
            self.assertEqual(max(item.bounds().width(), item.bounds().height()), 50)
            self.assertGreaterEqual(max(item.image.width(), item.image.height()), 256)

    def test_sticker_scaling_uses_the_normalized_size_and_shadow_is_tinted(self) -> None:
        sticker = Path(__file__).resolve().parents[1] / "ksnip_py" / "stickers" / "tutorial_attention.svg"
        canvas = AnnotationCanvas()
        background = QImage(160, 120, QImage.Format.Format_ARGB32)
        background.fill(QColor("white"))
        canvas.set_image(background)
        canvas.set_sticker_path(str(sticker))
        canvas.set_tool(Tool.STICKER)
        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(80, 60))
        canvas._items[0].image.fill(QColor("red"))

        bounds = canvas._items[0].bounds()
        shadow_pixel = canvas.image().pixelColor(bounds.right() + 1, bounds.center().y())
        self.assertLessEqual(abs(shadow_pixel.red() - shadow_pixel.green()), 2)
        self.assertLessEqual(abs(shadow_pixel.green() - shadow_pixel.blue()), 2)

        self.assertTrue(canvas.apply_scaling_to_selected_item(200))
        self.assertEqual(max(canvas._items[0].bounds().width(), canvas._items[0].bounds().height()), 100)

    def test_sticker_downscaling_uses_smooth_interpolation(self) -> None:
        sticker = Path(__file__).resolve().parents[1] / "ksnip_py" / "stickers" / "tutorial_attention.svg"
        background = QImage(100, 80, QImage.Format.Format_ARGB32)
        background.fill(QColor("white"))
        canvas = AnnotationCanvas()
        canvas.set_image(background)
        canvas.set_sticker_path(str(sticker))
        canvas.set_tool(Tool.STICKER)
        QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=QPoint(50, 40))

        source = QImage(2, 1, QImage.Format.Format_ARGB32)
        source.setPixelColor(0, 0, QColor("black"))
        source.setPixelColor(1, 0, QColor("white"))
        canvas._items[0].image = source
        canvas._items[0].shadow = False
        rendered = canvas.image()
        bounds = canvas._items[0].bounds()
        reds = [rendered.pixelColor(x, bounds.center().y()).red() for x in range(bounds.left(), bounds.right() + 1)]
        self.assertTrue(any(0 < value < 255 for value in reds))


if __name__ == "__main__":
    unittest.main()
