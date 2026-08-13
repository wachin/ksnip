import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QRect, QSettings, Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from ksnip_py.canvas import FillMode, Tool
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
    def test_tooltips_show_original_and_configurable_shortcuts(self) -> None:
        window = MainWindow()
        self.assertEqual(window.number_pointer_action.shortcut().toString(), "O")
        self.assertEqual(window.number_pointer_action.toolTip(), "Number Pointer (O)")
        self.assertEqual(window.pen_action.toolTip(), "Pen (P)")
        window._set_tool_group_default_action("number", window.number_pointer_action)
        self.assertEqual(window._tool_group_buttons["number"].toolTip(), "Number Pointer (O)")

        window._apply_shortcuts_from_mapping({"save": "Ctrl+Alt+S", "capture_rect": "Alt+R"})
        self.assertEqual(window.save_action.toolTip(), "Save (Ctrl+Alt+S)")
        self.assertEqual(window.capture_menu_button.toolTip(), "New Screenshot (Alt+R)")

    def test_property_controls_explain_their_effects(self) -> None:
        window = MainWindow()
        self.assertIn("Font size", window.font_size.toolTip())
        self.assertEqual(window.bold_button.toolTip(), "Bold")
        self.assertIn("thickness", window.stroke_width.toolTip())
        self.assertIn("triangular arrow tip", window.arrow_head_size.toolTip())
        self.assertIn("next numbered annotation", window.number_value.toolTip())

        window.set_tool(Tool.NUMBER_ARROW)
        arrow_head_actions = [
            action for action in window.properties_toolbar.actions()
            if hasattr(action, "defaultWidget")
            and action.defaultWidget() is window.property_arrow_head_group
        ]
        self.assertEqual(len(arrow_head_actions), 1)
        self.assertTrue(arrow_head_actions[0].isVisible())
        self.assertEqual(window.current_canvas()._arrow_head_size, window.arrow_head_size.value())

    def test_arrowhead_control_updates_freshly_drawn_selected_number_arrow(self) -> None:
        window = MainWindow()
        setting_key = "editor/number_arrow_head_size"
        old_value = window._settings.value(setting_key)
        canvas = window.current_canvas()
        try:
            canvas.set_image(QImage(200, 120, QImage.Format.Format_ARGB32))
            window.set_tool(Tool.NUMBER_ARROW)
            item = canvas._build_drag_item(
                Tool.NUMBER_ARROW,
                QPoint(40, 60),
                QPoint(170, 60),
                QRect(QPoint(40, 60), QPoint(170, 60)).normalized(),
            )
            canvas._items = [item]
            canvas._select_single_item(0)

            window._apply_arrow_head_size(11)

            self.assertEqual(canvas.tool(), Tool.NUMBER_ARROW)
            self.assertEqual(canvas._items[0].arrow_head_size, 11)
            self.assertEqual(canvas._arrow_head_size, 11)
            canvas.undo()
            self.assertNotEqual(canvas._items[0].arrow_head_size, 11)
        finally:
            if old_value is None:
                window._settings.remove(setting_key)
            else:
                window._settings.setValue(setting_key, old_value)

    def test_number_arrow_shaft_and_head_controls_update_independently(self) -> None:
        window = MainWindow()
        canvas = window.current_canvas()
        canvas.set_image(QImage(240, 140, QImage.Format.Format_ARGB32))
        window.set_tool(Tool.NUMBER_ARROW)
        item = canvas._build_drag_item(
            Tool.NUMBER_ARROW,
            QPoint(45, 70),
            QPoint(190, 70),
            QRect(QPoint(45, 70), QPoint(190, 70)).normalized(),
        )
        canvas._items = [item]
        canvas._select_single_item(0)
        original_head = item.arrow_head_size

        window._apply_stroke_width(1)
        self.assertEqual(item.pen_width, 1)
        self.assertEqual(item.arrow_head_size, original_head)

        window._apply_arrow_head_size(36)
        self.assertEqual(item.pen_width, 1)
        self.assertEqual(item.arrow_head_size, 36)

        rendered = QImage(240, 140, QImage.Format.Format_ARGB32_Premultiplied)
        rendered.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rendered)
        try:
            with patch.object(canvas, "_draw_arrow", wraps=canvas._draw_arrow) as draw_arrow:
                canvas._draw_number_arrow(painter, item)
                self.assertEqual(draw_arrow.call_args.kwargs["pen_width"], 1)
                self.assertEqual(draw_arrow.call_args.kwargs["arrow_head_size"], 36)
        finally:
            painter.end()

    def test_font_size_control_updates_freshly_drawn_number_arrow(self) -> None:
        window = MainWindow()
        canvas = window.current_canvas()
        canvas.set_image(QImage(240, 140, QImage.Format.Format_ARGB32))
        window.set_tool(Tool.NUMBER_ARROW)
        item = canvas._build_drag_item(
            Tool.NUMBER_ARROW,
            QPoint(45, 70),
            QPoint(190, 70),
            QRect(QPoint(45, 70), QPoint(190, 70)).normalized(),
        )
        canvas._items = [item]
        canvas._select_single_item(0)
        original_size = item.font_point_size

        window._apply_font_size(36)

        self.assertEqual(canvas.tool(), Tool.NUMBER_ARROW)
        self.assertEqual(item.font_point_size, 36)
        self.assertEqual(canvas._font_point_size, 36)
        self.assertGreater(item.number_badge_diameter(), 30)
        canvas.undo()
        self.assertEqual(canvas._items[0].font_point_size, original_size)

    def test_new_canvas_numbering_starts_at_one_despite_legacy_setting(self) -> None:
        window = MainWindow()
        window._settings.setValue("editor/number_seed", 10)
        window._restore_ui_settings()
        self.assertEqual(window.number_value.value(), 1)
        self.assertFalse(window._settings.contains("editor/number_seed"))

        window.current_canvas().set_number_seed(10)
        new_canvas = window.new_tab()
        self.assertEqual(new_canvas.number_seed(), 1)

    def test_default_save_format_can_switch_between_png_and_ksnip(self) -> None:
        window = MainWindow()
        setting_key = "saver/default_format"
        old_value = window._settings.value(setting_key)
        try:
            window._settings.remove(setting_key)
            self.assertEqual(window._default_save_spec(), (".png", "PNG (*.png)"))
            window._settings.setValue(setting_key, "ksnip")
            self.assertEqual(
                window._default_save_spec(),
                (".ksnip", "Ksnip Project (*.ksnip)"),
            )
            window._settings.setValue(setting_key, "unsupported")
            self.assertEqual(window._default_save_spec(), (".png", "PNG (*.png)"))
        finally:
            if old_value is None:
                window._settings.remove(setting_key)
            else:
                window._settings.setValue(setting_key, old_value)

    def test_saving_project_also_saves_configured_companion_image(self) -> None:
        window = MainWindow()
        setting_key = "saver/project_companion_format"
        old_value = window._settings.value(setting_key)
        try:
            window._settings.setValue(setting_key, "png")
            with tempfile.TemporaryDirectory() as directory:
                project_path = Path(directory) / "tutorial.ksnip"
                canvas = window.current_canvas()
                image = QImage(80, 50, QImage.Format.Format_ARGB32)
                image.fill(QColor("white"))
                canvas.set_image(image)
                self.assertTrue(
                    window._save_canvas_to_path(
                        canvas,
                        window.tabs.currentIndex(),
                        str(project_path),
                        show_status=False,
                    )
                )
                companion_path = project_path.with_suffix(".png")
                self.assertTrue(project_path.is_file())
                self.assertTrue(companion_path.is_file())
                companion = QImage(str(companion_path))
                self.assertFalse(companion.isNull())
                self.assertEqual(companion.size(), canvas.image().size())
        finally:
            if old_value is None:
                window._settings.remove(setting_key)
            else:
                window._settings.setValue(setting_key, old_value)

    def test_controls_widget_exposes_the_cpp_actions_in_a_hidden_bottom_toolbar(self) -> None:
        window = MainWindow()
        self.assertEqual(
            window.controls_toolbar.actions(),
            [
                window.undo_action, window.redo_action, window.crop_action,
                window.scale_action, window.rotate_action,
                window.modify_canvas_action, window.cut_action,
            ],
        )
        self.assertEqual(window.toolBarArea(window.controls_toolbar), Qt.ToolBarArea.BottomToolBarArea)

    def test_annotation_tool_is_restored_only_when_remembering_is_enabled(self) -> None:
        window = MainWindow()
        settings = window._settings
        keys = ("editor/remember_tool", "editor/tool")
        old_values = {key: settings.value(key) for key in keys}
        try:
            settings.setValue("editor/remember_tool", False)
            settings.setValue("editor/tool", Tool.ELLIPSE.value)
            window._apply_tool_selection_from_settings()
            self.assertEqual(window.current_canvas().tool(), Tool.PEN)

            settings.setValue("editor/remember_tool", True)
            settings.setValue("editor/tool", Tool.ELLIPSE.value)
            window._apply_tool_selection_from_settings()
            self.assertEqual(window.current_canvas().tool(), Tool.ELLIPSE)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)

    def test_visible_menu_actions_have_icons_even_without_a_full_desktop_theme(self) -> None:
        window = MainWindow()
        action_names = (
            "copy_data_uri_action", "copy_path_action", "rename_action", "open_directory_action",
            "copy_item_action", "close_tab_action", "paste_item_action", "edit_text_action",
            "bring_to_front_action", "send_to_back_action", "modify_canvas_action", "toggle_docks_action",
            "add_watermark_action", "upload_action", "ocr_action", "update_watermark_action",
            "rotate_watermark_action", "settings_action", "about_action", "clear_recent_images_action",
            "zoom_out_action", "zoom_in_action",
        )
        self.assertTrue(all(not getattr(window, name).icon().isNull() for name in action_names))

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

    def test_bottom_bar_exposes_modify_canvas_and_current_image_effect(self) -> None:
        window = MainWindow()
        self.assertIs(window.bottom_modify_canvas_button.defaultAction(), window.modify_canvas_action)
        self.assertEqual(len(window.bottom_effect_button.menu().actions()), 6)
        self.assertFalse(window.bottom_effect_button.isEnabled())

        canvas = window.current_canvas()
        canvas.set_image(QImage(20, 20, QImage.Format.Format_ARGB32))
        window._update_actions()
        self.assertTrue(window.bottom_effect_button.isEnabled())
        window.grayscale_action.trigger()
        self.assertEqual(canvas.image_effect(), "grayscale")
        self.assertEqual(window.bottom_effect_button.icon().cacheKey(), window.grayscale_action.icon().cacheKey())

    def test_item_settings_uses_a_second_toolbar_row_and_keeps_only_handle_when_empty(self) -> None:
        window = MainWindow()
        window.set_tool(Tool.SELECT)
        self.assertFalse(window.properties_toolbar.isHidden())
        self.assertEqual(len(window.properties_toolbar.actions()), 1)
        window.set_tool(Tool.ARROW)
        self.assertFalse(window.properties_toolbar.isHidden())
        self.assertGreater(len(window.properties_toolbar.actions()), 1)
        self.assertTrue(window.toolBarBreak(window.properties_toolbar))

    def test_duplicate_tool_is_selectable_and_exposes_only_opacity(self) -> None:
        window = MainWindow()
        window.duplicate_tool_action.trigger()
        self.assertEqual(window.current_canvas().tool(), Tool.DUPLICATE)
        controls = [
            widget for action in window.properties_toolbar.actions()
            if (widget := window.properties_toolbar.widgetForAction(action)) in window._property_groups.values()
        ]
        self.assertEqual(controls, [window.property_handle_group, window.property_opacity_group])
        self.assertEqual(window.duplicate_tool_action.shortcut().toString(), "U")

    def test_tool_widths_use_cpp_defaults_and_are_restored_per_tool(self) -> None:
        window = MainWindow()
        settings = window._settings
        marker_key = "editor/tool_width/marker_pen"
        arrow_key = "editor/tool_width/arrow"
        old_marker = settings.value(marker_key)
        old_arrow = settings.value(arrow_key)
        try:
            settings.remove(marker_key)
            settings.remove(arrow_key)
            window.set_tool(Tool.MARKER_PEN)
            self.assertEqual(window.stroke_width.maximum(), 100)
            self.assertEqual(window.stroke_width.value(), 30)
            window.stroke_width.setValue(44)
            window.set_tool(Tool.ARROW)
            self.assertEqual(window.stroke_width.maximum(), 20)
            self.assertEqual(window.stroke_width.value(), 6)
            window.set_tool(Tool.MARKER_PEN)
            self.assertEqual(window.stroke_width.value(), 44)
        finally:
            if old_marker is None:
                settings.remove(marker_key)
            else:
                settings.setValue(marker_key, old_marker)
            if old_arrow is None:
                settings.remove(arrow_key)
            else:
                settings.setValue(arrow_key, old_arrow)

    def test_shadow_and_opacity_are_restored_per_tool_with_cpp_defaults(self) -> None:
        window = MainWindow()
        settings = window._settings
        keys = [
            "editor/tool_shadow/pen", "editor/tool_opacity/pen",
            "editor/tool_shadow/arrow", "editor/tool_opacity/arrow",
            "editor/tool_shadow/text_arrow", "editor/tool_opacity/text_arrow",
        ]
        old_values = {key: settings.value(key) for key in keys}
        try:
            for key in keys:
                settings.remove(key)
            window.set_tool(Tool.PEN)
            self.assertTrue(window.shadow_state_button.isChecked())
            self.assertEqual(window.opacity.value(), 100)
            window.shadow_state_button.setChecked(False)
            window.opacity.setValue(35)

            window.set_tool(Tool.ARROW)
            self.assertTrue(window.shadow_state_button.isChecked())
            self.assertEqual(window.opacity.value(), 100)
            window.set_tool(Tool.TEXT_ARROW)
            self.assertFalse(window.shadow_state_button.isChecked())
            self.assertEqual(window.opacity.value(), 100)

            window.set_tool(Tool.PEN)
            self.assertFalse(window.shadow_state_button.isChecked())
            self.assertEqual(window.opacity.value(), 35)
            self.assertFalse(window.current_canvas()._shadow)
            self.assertEqual(window.current_canvas()._opacity, 0.35)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)

    def test_colors_use_cpp_defaults_and_are_restored_per_tool(self) -> None:
        window = MainWindow()
        settings = window._settings
        tools = (Tool.MARKER_PEN, Tool.LINE, Tool.RECT, Tool.TEXT, Tool.ARROW)
        keys = [f"editor/tool_color/{tool.value}" for tool in tools]
        old_values = {key: settings.value(key) for key in keys}
        try:
            for key in keys:
                settings.remove(key)
            expected = {
                Tool.MARKER_PEN: QColor(Qt.GlobalColor.yellow),
                Tool.LINE: QColor(Qt.GlobalColor.blue),
                Tool.RECT: QColor(Qt.GlobalColor.gray),
                Tool.TEXT: QColor(Qt.GlobalColor.black),
                Tool.ARROW: QColor(Qt.GlobalColor.red),
            }
            for tool, color in expected.items():
                window.set_tool(tool)
                self.assertEqual(window.current_canvas().color(), color)

            custom = QColor(12, 34, 56, 180)
            window.set_tool(Tool.ARROW)
            window._apply_selected_color(custom)
            window.set_tool(Tool.LINE)
            window.set_tool(Tool.ARROW)
            self.assertEqual(window.current_canvas().color(), custom)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)

    def test_fill_modes_use_port_defaults_and_are_restored_per_tool(self) -> None:
        window = MainWindow()
        settings = window._settings
        tools = (Tool.TEXT, Tool.NUMBER, Tool.NUMBER_ARROW, Tool.RECT, Tool.ELLIPSE)
        keys = [f"editor/tool_fill_mode/{tool.value}" for tool in tools]
        old_values = {key: settings.value(key) for key in keys}
        try:
            for key in keys:
                settings.remove(key)
            expected = {
                Tool.TEXT: FillMode.BORDER_AND_NO_FILL,
                Tool.NUMBER: FillMode.BORDER_AND_FILL,
                Tool.NUMBER_ARROW: FillMode.BORDER_AND_FILL,
                Tool.RECT: FillMode.BORDER_AND_FILL,
                Tool.ELLIPSE: FillMode.BORDER_AND_NO_FILL,
            }
            for tool, fill_mode in expected.items():
                window.set_tool(tool)
                self.assertEqual(window.fill_mode.currentData(), fill_mode)
                self.assertEqual(window.current_canvas()._fill_mode, fill_mode)

            window.set_tool(Tool.TEXT)
            window.fill_mode.setCurrentIndex(window.fill_mode.findData(FillMode.BORDER_AND_FILL))
            window.set_tool(Tool.RECT)
            window.set_tool(Tool.TEXT)
            self.assertEqual(window.fill_mode.currentData(), FillMode.BORDER_AND_FILL)

            settings.setValue("editor/tool_fill_mode/rect", FillMode.NO_BORDER_AND_NO_FILL.value)
            window.set_tool(Tool.RECT)
            self.assertEqual(window.fill_mode.currentData(), FillMode.BORDER_AND_FILL)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)

    def test_text_colors_use_cpp_default_and_are_restored_per_tool(self) -> None:
        window = MainWindow()
        settings = window._settings
        tools = (Tool.TEXT, Tool.TEXT_POINTER, Tool.TEXT_ARROW, Tool.NUMBER, Tool.NUMBER_POINTER, Tool.NUMBER_ARROW)
        keys = [f"editor/tool_text_color/{tool.value}" for tool in tools]
        old_values = {key: settings.value(key) for key in keys}
        try:
            for key in keys:
                settings.remove(key)
            for tool in tools:
                window.set_tool(tool)
                self.assertEqual(window.current_canvas().text_color(), QColor(Qt.GlobalColor.white))

            text_color = QColor(20, 40, 60, 180)
            number_color = QColor(210, 190, 170, 150)
            window.set_tool(Tool.TEXT)
            window._apply_selected_text_color(text_color)
            window.set_tool(Tool.NUMBER)
            window._apply_selected_text_color(number_color)
            window.set_tool(Tool.TEXT)
            self.assertEqual(window.current_canvas().text_color(), text_color)
            window.set_tool(Tool.NUMBER)
            self.assertEqual(window.current_canvas().text_color(), number_color)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)

    def test_fonts_use_cpp_defaults_and_are_restored_per_tool(self) -> None:
        window = MainWindow()
        settings = window._settings
        tools = (Tool.TEXT, Tool.NUMBER)
        suffixes = ("family", "size", "bold", "italic", "underline")
        keys = [f"editor/tool_font/{tool.value}/{suffix}" for tool in tools for suffix in suffixes]
        old_values = {key: settings.value(key) for key in keys}
        try:
            for key in keys:
                settings.remove(key)
            window.set_tool(Tool.TEXT)
            self.assertEqual(window.font_size.value(), 15)
            self.assertTrue(window.bold_button.isChecked())
            self.assertFalse(window.italic_button.isChecked())
            window.font_size.setValue(17)
            window.bold_button.setChecked(False)
            window.italic_button.setChecked(True)
            window.underline_button.setChecked(True)

            window.set_tool(Tool.NUMBER)
            self.assertEqual(window.font_size.value(), 20)
            self.assertTrue(window.bold_button.isChecked())
            self.assertFalse(window.italic_button.isChecked())
            self.assertFalse(window.underline_button.isChecked())

            window.set_tool(Tool.TEXT)
            self.assertEqual(window.font_size.value(), 17)
            self.assertFalse(window.bold_button.isChecked())
            self.assertTrue(window.italic_button.isChecked())
            self.assertTrue(window.underline_button.isChecked())
            canvas = window.current_canvas()
            self.assertEqual(canvas._font_point_size, 17)
            self.assertFalse(canvas._bold)
            self.assertTrue(canvas._italic)
            self.assertTrue(canvas._underline)
        finally:
            for key, value in old_values.items():
                if value is None:
                    settings.remove(key)
                else:
                    settings.setValue(key, value)


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
            ["Original", "Papirus", "GNOME", "Numix", "SuperTux", "TuxBaby", "User"],
        )
        self.assertEqual(collections[1].directory, collections[0].directory / "themes" / "papirus")
        self.assertEqual(collections[2].directory, collections[0].directory / "themes" / "gnome")
        self.assertEqual(collections[3].directory, collections[0].directory / "themes" / "numix")
        self.assertEqual(collections[4].directory, collections[0].directory / "themes" / "supertux")
        self.assertEqual(collections[5].directory, collections[0].directory / "themes" / "tuxbaby")
        self.assertEqual(collections[6].directory, user_sticker_directory())
        self.assertTrue(all(discover_stickers(collection.directory) for collection in collections[1:6]))
        supertux_names = {path.name for path in discover_stickers(collections[4].directory)}
        self.assertEqual(len(supertux_names), 26)
        self.assertIn("smiling_face_with_sunglasses.svg", supertux_names)
        self.assertIn("tutorial_terminal.svg", supertux_names)
        tuxbaby_names = {path.name for path in discover_stickers(collections[5].directory)}
        self.assertEqual(len(tuxbaby_names), 33)
        self.assertIn("smiling_face.png", tuxbaby_names)
        self.assertIn("tutorial_terminal.png", tuxbaby_names)
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
