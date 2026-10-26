import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import AnnotationCanvas, FillMode, OverlayItem, Tool
from ksnip_py.project_io import export_svg, load_project, save_project


APP = QApplication.instance() or QApplication([])


def plain_image(width: int = 200, height: int = 150) -> QImage:
    image = QImage(width, height, QImage.Format.Format_ARGB32)
    image.fill(QColor("white"))
    return image


class RotationHandleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(plain_image())

    def _rect(self, rotation: int = 0) -> OverlayItem:
        return OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(70, 70),
            color=QColor("red"), pen_width=2, rotation=rotation,
        )

    def test_rotated_handle_points_include_rotate_for_rect(self) -> None:
        points = self.canvas._rotated_handle_points(self._rect())
        self.assertIn("rotate", points)
        # rotate handle sits above the item center (22px along the up axis)
        self.assertEqual(points["rotate"], QPoint(50, 28))

    def test_rotated_handle_points_include_rotate_for_line(self) -> None:
        line = OverlayItem(
            kind=Tool.ARROW, start=QPoint(10, 50), end=QPoint(110, 50),
            color=QColor("red"), pen_width=2,
        )
        points = self.canvas._rotated_handle_points(line)
        self.assertIn("rotate", points)

    def test_pen_items_have_a_rotate_handle(self) -> None:
        pen = OverlayItem(
            kind=Tool.PEN, start=QPoint(0, 0), end=QPoint(0, 0),
            color=QColor("red"), pen_width=2,
            points=[QPoint(10, 10), QPoint(40, 30), QPoint(60, 10)],
        )
        self.assertIn("rotate", self.canvas._rotated_handle_points(pen))

    def test_rotated_pen_is_hit_tested_in_local_frame(self) -> None:
        pen = OverlayItem(
            kind=Tool.PEN, start=QPoint(0, 0), end=QPoint(0, 0),
            color=QColor("red"), pen_width=2, rotation=90,
            points=[QPoint(0, 0), QPoint(100, 0)],
        )
        self.canvas._items = [pen]
        # after rotating the horizontal scribble 90 deg it lies along x=50
        self.assertEqual(self.canvas._find_item_at(QPoint(50, 25)), 0)
        self.assertIsNone(self.canvas._find_item_at(QPoint(10, 10)))

    def test_find_handle_at_returns_rotate(self) -> None:
        item = self._rect()
        rotate_pt = self.canvas._rotated_handle_points(item)["rotate"]
        self.assertEqual(self.canvas._find_handle_at(item, rotate_pt), "rotate")


class RotationMathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(plain_image())

    def _rect(self) -> OverlayItem:
        return OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(70, 70),
            color=QColor("red"), pen_width=2,
        )

    def test_rotating_pointer_changes_rotation(self) -> None:
        item = self._rect()
        # pointer straight above center -> -90 deg start angle
        self.canvas._begin_handle_drag(item, "rotate", QPoint(50, 18))
        # pointer to the right of center -> 0 deg current angle => 90 deg delta
        self.canvas._rotate_item_to_pointer(item, QPoint(90, 50), snap=False)
        self.assertEqual(item.rotation, 90)

    def test_rotation_wraps_with_modulo_360(self) -> None:
        item = self._rect()
        self.canvas._begin_handle_drag(item, "rotate", QPoint(50, 18))
        # 270 deg delta -> 270
        self.canvas._rotate_item_to_pointer(item, QPoint(10, 50), snap=False)
        self.assertEqual(item.rotation, 270)

    def test_shift_snaps_to_15_degrees(self) -> None:
        item = self._rect()
        self.canvas._begin_handle_drag(item, "rotate", QPoint(50, 18))
        # yields ~63.4 deg, snaps to 60
        self.canvas._rotate_item_to_pointer(item, QPoint(90, 20), snap=True)
        self.assertEqual(item.rotation, 60)

    def test_find_item_at_respects_rotation(self) -> None:
        line = OverlayItem(
            kind=Tool.LINE, start=QPoint(0, 0), end=QPoint(100, 0),
            color=QColor("red"), pen_width=2, rotation=90,
        )
        self.canvas._items = [line]
        # after 90 deg rotation the line is vertical through (50, 0)
        self.assertEqual(self.canvas._find_item_at(QPoint(50, 25)), 0)
        # a point far from the rotated line is not hit
        self.assertIsNone(self.canvas._find_item_at(QPoint(10, 10)))


class RotationRenderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(plain_image())

    def test_draw_item_renders_with_rotation(self) -> None:
        image = QImage(200, 150, QImage.Format.Format_ARGB32)
        painter = QPainter(image)
        item = OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(70, 70),
            color=QColor("red"), pen_width=2, rotation=45,
        )
        try:
            self.canvas._draw_item(painter, item, True)
        finally:
            painter.end()
        self.assertFalse(image.isNull())


class RotationPersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(plain_image())
        self.item = OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(70, 70),
            color=QColor("red"), pen_width=2, rotation=45,
        )
        self.canvas._items = [self.item]

    def test_project_round_trip_preserves_rotation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "rotated.ksnip")
            save_project(path, self.canvas)
            image, metadata = load_project(path)
            restored = AnnotationCanvas()
            restored.restore_project(image, metadata, path)
            self.assertEqual(restored._items[0].rotation, 45)

    def test_svg_export_includes_rotation_transform(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rotated.svg"
            export_svg(str(path), self.canvas)
            svg = path.read_text(encoding="utf-8")
        # center of (30,30)-(70,70) is (50,50); rotation is 45 deg
        self.assertIn("rotate(45 50.0 50.0)", svg)


class RotationMouseInteractionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        image = plain_image(200, 150)
        self.canvas.set_image(image)
        self.canvas.resize(200, 150)
        self.canvas.set_tool(Tool.SELECT)
        self.canvas._items = [
            OverlayItem(
                kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(70, 70),
                color=QColor("red"), pen_width=2,
            ),
        ]
        self.canvas._select_single_item(0)
        self.canvas._refresh()

    def _rotate_handle_widget_pos(self) -> QPoint:
        item = self.canvas._items[0]
        return self.canvas._rotated_handle_points(item)["rotate"]

    def test_drag_rotate_handle_rotates_item_and_records_undo(self) -> None:
        handle = self._rotate_handle_widget_pos()
        self.assertEqual(handle, QPoint(50, 28))

        QTest.mousePress(self.canvas, Qt.MouseButton.LeftButton, pos=handle)
        QTest.mouseMove(self.canvas, QPoint(90, 50))
        QTest.mouseRelease(self.canvas, Qt.MouseButton.LeftButton, pos=QPoint(90, 50))

        self.assertEqual(self.canvas._items[0].rotation, 90)
        self.assertEqual(len(self.canvas._undo_stack), 1)

        self.canvas.undo()
        self.assertEqual(self.canvas._items[0].rotation, 0)



class RotatedStickerShadowTest(unittest.TestCase):
    """The drop shadow of an image-based item must rotate with the item, not
    linger at the pre-rotation position (which previously left a dark remnant)."""

    def setUp(self) -> None:
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(plain_image())

    def _render_sticker(self, rotation: int) -> QImage:
        image = QImage(200, 150, QImage.Format.Format_ARGB32)
        image.fill(QColor('white'))
        painter = QPainter(image)
        sticker = OverlayItem(
            kind=Tool.STICKER, start=QPoint(30, 30), end=QPoint(90, 50),
            color=QColor('red'), pen_width=2, rotation=rotation, shadow=True,
        )
        sticker.image = QImage(60, 20, QImage.Format.Format_ARGB32)
        sticker.image.fill(QColor('white'))
        try:
            self.canvas._draw_item(painter, sticker, False)
        finally:
            painter.end()
        return image

    def test_shadow_darkens_unrotated_position_when_not_rotated(self) -> None:
        image = self._render_sticker(0)
        self.assertLess(image.pixelColor(92, 42).red(), 150)

    def test_shadow_follows_rotation_and_leaves_no_remnant(self) -> None:
        image = self._render_sticker(90)
        self.assertGreater(image.pixelColor(92, 42).red(), 200)
        self.assertLess(image.pixelColor(48, 40).red(), 150)



class RotationDragGhostingTest(unittest.TestCase):
    """A real rotate-handle drag repaints every frame from scratch, so no
    intermediate angle should leave a trail. We sweep the handle through
    several angles and assert each live frame equals a clean re-render of
    the current angle (same _refresh path, no accumulated pixels)."""

    def setUp(self) -> None:
        self.bg = QImage(200, 150, QImage.Format.Format_ARGB32)
        self.bg.fill(QColor('white'))
        self.canvas = AnnotationCanvas()
        self.canvas.set_image(self.bg)
        self.canvas.resize(200, 150)
        self.canvas.set_tool(Tool.SELECT)
        self.item = OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(80, 70),
            color=QColor('red'), pen_width=3,
        )
        self.canvas._items = [self.item]
        self.canvas._select_single_item(0)
        self.canvas._refresh()

    def _clean_render(self, rotation: int) -> QImage:
        c = AnnotationCanvas()
        c.set_image(self.bg)
        c.resize(200, 150)
        it = OverlayItem(
            kind=Tool.RECT, start=QPoint(30, 30), end=QPoint(80, 70),
            color=QColor('red'), pen_width=3, rotation=rotation,
        )
        c._items = [it]
        c._select_single_item(0)
        c._refresh()
        return c.pixmap().toImage()

    def _diff_fraction(self, a: QImage, b: QImage) -> float:
        total = a.width() * a.height()
        if total == 0:
            return 1.0
        diff = 0
        for y in range(a.height()):
            for x in range(a.width()):
                if a.pixelColor(x, y) != b.pixelColor(x, y):
                    diff += 1
        return diff / total

    def test_drag_sweep_leaves_no_ghost_trails(self) -> None:
        handle = self.canvas._rotated_handle_points(self.item)['rotate']
        QTest.mousePress(self.canvas, Qt.MouseButton.LeftButton, pos=handle)
        targets = [QPoint(120, 50), QPoint(50, 110), QPoint(0, 50), QPoint(50, 0)]
        for index, target in enumerate(targets):
            QTest.mouseMove(self.canvas, target)
            live = self.canvas.pixmap().toImage()
            clean = self._clean_render(self.canvas._items[0].rotation)
            self.assertEqual(live.size(), clean.size())
            frac = self._diff_fraction(live, clean)
            self.assertLess(frac, 0.03, f"possible ghost trail at step {index}: {frac:.3f}")
        QTest.mouseRelease(self.canvas, Qt.MouseButton.LeftButton, pos=targets[-1])


if __name__ == "__main__":
    unittest.main()
