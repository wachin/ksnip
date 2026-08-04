import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtGui import QColor, QIcon, QImage
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import Tool
from ksnip_py.color_picker import ColorPaletteMenu
from ksnip_py.main_window import MainWindow, migrate_normalized_sticker_scaling
from ksnip_py.sticker_picker import (
    StickerCollection,
    StickerPickerDialog,
    discover_stickers,
    import_user_sticker,
    sticker_collections,
    user_sticker_directory,
)


APP = QApplication.instance() or QApplication([])


class ColorPaletteMenuTest(unittest.TestCase):
    def test_default_palette_matches_kcolorpicker(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        self.assertEqual(len(palette._colors), 12)
        expected = [QColor(color) for color in (Qt.GlobalColor.red, Qt.GlobalColor.green, Qt.GlobalColor.blue, Qt.GlobalColor.yellow, Qt.GlobalColor.magenta, Qt.GlobalColor.cyan, Qt.GlobalColor.white, Qt.GlobalColor.black)]
        self.assertEqual(palette._colors[:8], expected)
        self.assertTrue(all(color.alpha() == 100 for color in palette._colors[8:]))

    def test_custom_color_is_added_and_selected(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        custom = QColor(12, 34, 56, 78)
        palette.select_color(custom)
        self.assertIn(custom, palette._colors)
        self.assertTrue(any(button.isChecked() for button in palette._buttons))

    def test_marker_mode_removes_alpha_choices(self) -> None:
        palette = ColorPaletteMenu(show_alpha=True)
        palette.select_color(QColor(12, 34, 56, 78))
        palette.set_show_alpha(False)
        self.assertEqual(len(palette._colors), 9)
        self.assertTrue(all(color.alpha() == 255 for color in palette._colors))


class MainWindowColorPickerTest(unittest.TestCase):
    def test_bundled_stickers_are_loaded_from_the_python_package(self) -> None:
        window = MainWindow()
        paths = [Path(path) for path in window._default_sticker_paths()]
        self.assertEqual(len(paths), 26)
        self.assertTrue(all(path.parent.name == "stickers" for path in paths))
        self.assertTrue(all(path.parent.parent.name == "ksnip_py" for path in paths))
        self.assertTrue(all(not QIcon(str(path)).isNull() for path in paths))
        self.assertIn("check_mark.svg", {path.name for path in paths})
        self.assertIn("smiling_face_with_sunglasses.svg", {path.name for path in paths})
        self.assertIn("tutorial_attention.svg", {path.name for path in paths})
        self.assertIn("tutorial_terminal.svg", {path.name for path in paths})

    def test_palette_applies_and_synchronizes_stroke_color(self) -> None:
        window = MainWindow()
        image = QImage(20, 20, QImage.Format.Format_ARGB32)
        image.fill(QColor("white"))
        canvas = window.current_canvas()
        canvas.set_image(image)
        selected = QColor(23, 45, 67, 120)
        window._apply_selected_color(selected)
        self.assertEqual(canvas.color(), selected)
        self.assertIn(selected, window.property_color_palette._colors)
        self.assertIn(selected, window.toolbox_color_palette._colors)

        window.set_tool(Tool.MARKER_PEN)
        self.assertTrue(all(color.alpha() == 255 for color in window.property_color_palette._colors))

    def test_zoom_picker_matches_the_original_controls_and_shortcuts(self) -> None:
        window = MainWindow()
        self.assertEqual(window.zoom_spinbox.minimum(), 10)
        self.assertEqual(window.zoom_spinbox.maximum(), 800)
        self.assertEqual(window.zoom_spinbox.singleStep(), 10)
        self.assertFalse(window.zoom_fit_button.isHidden())
        self.assertFalse(window.zoom_reset_button.isHidden())
        self.assertEqual(window.zoom_reset_action.shortcut().toString(), "Ctrl+0")
        self.assertEqual(window.zoom_fit_action.shortcut().toString(), "Ctrl+F")
        self.assertFalse(window.zoom_in_action.shortcut().isEmpty())
        self.assertFalse(window.zoom_out_action.shortcut().isEmpty())
        canvas = window.current_canvas()
        canvas.set_image(QImage(20, 20, QImage.Format.Format_ARGB32))
        window._update_actions()
        window.zoom_in_action.trigger()
        self.assertEqual(canvas.zoom_percent(), 110)
        self.assertEqual(window.zoom_spinbox.value(), 110)
        window.zoom_reset_action.trigger()
        self.assertEqual(canvas.zoom_percent(), 100)


class StickerPickerTest(unittest.TestCase):
    def test_legacy_sticker_scaling_is_migrated_to_the_normalized_default_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / "settings.ini"), QSettings.Format.IniFormat)
            settings.setValue("editor/scaling_percent", 160)
            self.assertTrue(migrate_normalized_sticker_scaling(settings))
            self.assertEqual(settings.value("editor/scaling_percent", type=int), 100)
            settings.setValue("editor/scaling_percent", 140)
            self.assertFalse(migrate_normalized_sticker_scaling(settings))
            self.assertEqual(settings.value("editor/scaling_percent", type=int), 140)

    def test_expected_theme_directories_are_exposed(self) -> None:
        collections = sticker_collections()
        self.assertEqual(
            [collection.name for collection in collections],
            ["Original", "Papirus", "GNOME", "Numix", "SuperTux", "User"],
        )
        self.assertEqual(collections[1].directory, collections[0].directory / "themes" / "papirus")
        self.assertEqual(collections[2].directory, collections[0].directory / "themes" / "gnome")
        self.assertEqual(collections[3].directory, collections[0].directory / "themes" / "numix")
        self.assertEqual(collections[4].directory, collections[0].directory / "themes" / "supertux")
        self.assertEqual(collections[5].directory, user_sticker_directory())
        self.assertEqual([len(discover_stickers(collection.directory)) for collection in collections[1:4]], [49, 44, 58])
        original_names = {path.name for path in discover_stickers(collections[0].directory)}
        for collection in collections[1:5]:
            names = {path.name for path in discover_stickers(collection.directory)}
            self.assertTrue(original_names.issubset(names))
            self.assertIn("check_mark.svg", names)
            self.assertIn("cross_mark.svg", names)
        supertux_names = {path.name for path in discover_stickers(collections[4].directory)}
        self.assertEqual(len(supertux_names), 26)
        self.assertIn("smiling_face_with_sunglasses.svg", supertux_names)
        self.assertIn("tutorial_terminal.svg", supertux_names)
        for collection in collections[1:5]:
            if collection.directory.is_dir():
                self.assertTrue(all(not path.is_symlink() for path in discover_stickers(collection.directory)))

    def test_discovery_excludes_symbolic_links_and_unsupported_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real.svg"
            real.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
            (root / "duplicate.svg").symlink_to(real.name)
            (root / "notes.txt").write_text("not a sticker", encoding="utf-8")
            self.assertEqual(discover_stickers(root), [real])

    def test_user_sticker_import_is_png_bounded_and_uniquely_named(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "Mi imagen grande.webp"
            image = QImage(1024, 256, QImage.Format.Format_ARGB32)
            image.fill(QColor(20, 40, 60, 128))
            self.assertTrue(image.save(str(source), "WEBP"))

            first = import_user_sticker(source, root / "saved")
            second = import_user_sticker(source, root / "saved")

            self.assertEqual(first, root / "saved" / "Mi_imagen_grande.png")
            self.assertEqual(second, root / "saved" / "Mi_imagen_grande_2.png")
            imported = QImage(str(first))
            self.assertEqual((imported.width(), imported.height()), (512, 128))
            self.assertTrue(imported.hasAlphaChannel())

    def test_invalid_user_sticker_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "broken.png"
            source.write_text("not an image", encoding="utf-8")
            self.assertIsNone(import_user_sticker(source, root / "saved"))

    def test_favorites_are_persistent_and_visible_independently_of_tabs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sticker = root / "favorite.svg"
            sticker.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>', encoding="utf-8")
            settings = QSettings(str(root / "settings.ini"), QSettings.Format.IniFormat)
            collections = (StickerCollection("Test", root),)
            dialog = StickerPickerDialog(settings=settings, collections=collections)
            dialog._toggle_favorite(str(sticker), True)
            restored = StickerPickerDialog(settings=settings, collections=collections)
            self.assertEqual(restored.favorite_paths(), [str(sticker)])
            self.assertGreater(restored._favorites_layout.count(), 0)
            restored._toggle_favorite(str(sticker), False)
            self.assertEqual(StickerPickerDialog(settings=settings, collections=collections).favorite_paths(), [])

    def test_last_theme_tab_is_restored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / "settings.ini"), QSettings.Format.IniFormat)
            collections = tuple(StickerCollection(name, Path(directory)) for name in ("Original", "Papirus", "GNOME", "Numix"))
            dialog = StickerPickerDialog(settings=settings, collections=collections)
            dialog.tabs.setCurrentIndex(2)
            self.assertEqual(settings.value(StickerPickerDialog.LAST_TAB_KEY), "GNOME")
            restored = StickerPickerDialog(settings=settings, collections=collections)
            self.assertEqual(restored.tabs.tabText(restored.tabs.currentIndex()), "GNOME")


if __name__ == "__main__":
    unittest.main()
