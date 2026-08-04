from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import sys

from PyQt6.QtCore import QBuffer, QEvent, QEventLoop, QIODevice, QPoint, QRectF, QSettings, QSize, QThread, QTimer, Qt, QUrl
from PyQt6.QtGui import QAction, QActionGroup, QColor, QDesktopServices, QFont, QGuiApplication, QIcon, QImage, QKeySequence, QPainter, QPixmap
from PyQt6.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFontComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QMenu,
    QProgressDialog,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .canvas import AnnotationCanvas, CutDialog, FillMode, ModifyCanvasDialog, RotateDialog, ScaleDialog, Tool
from .color_picker import ColorPaletteMenu
from .capture import (
    grab_active_window,
    grab_current_screen,
    grab_fullscreen,
    grab_last_rectangular_area,
    grab_portal,
    grab_rectangular_area,
    grab_window_under_cursor,
    grab_x11_cursor,
    has_last_rectangular_area,
    is_wayland_session,
    portal_capture_was_canceled,
    portal_failure_message,
)
from .ocr_backend import OcrBackend, OcrOptions, OcrWorker
from .ocr_result_dialog import OcrResultDialog
from .pin_window import PinWindow
from .settings_dialog import SettingsData, SettingsDialog
from .spellcheck import load_spellcheck_scheme, save_spellcheck_scheme
from .sticker_picker import StickerPickerDialog
from .uploader import ScriptUploader
from .watermark import WatermarkPreparer, WatermarkStore, random_watermark_position


def migrate_normalized_sticker_scaling(settings: QSettings) -> bool:
    migration_key = "editor/normalized_sticker_size_v1"
    migrated = str(settings.value(migration_key, "false")).lower() in {"true", "1", "yes"}
    if migrated:
        return False
    settings.setValue("editor/scaling_percent", 100)
    settings.setValue(migration_key, True)
    settings.sync()
    return True


class MainWindow(QMainWindow):
    MAX_RECENT_IMAGES = 10

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings()
        self._docks_collapsed = False
        self._property_toolbar_has_controls = False
        migrate_normalized_sticker_scaling(self._settings)
        self._recent_image_paths = self._load_recent_image_paths()
        self._pin_windows: list[PinWindow] = []
        self._watermark_store = WatermarkStore()
        self._watermark_preparer = WatermarkPreparer()
        self._script_uploader = ScriptUploader()
        self._ocr_backend = OcrBackend()
        self._ocr_thread: QThread | None = None
        self._ocr_worker: OcrWorker | None = None
        self._ocr_progress: QProgressDialog | None = None
        self._tray_icon: QSystemTrayIcon | None = None
        self._allow_quit = False
        self._capture_delay_override_seconds: int | None = None
        self._capture_cursor_override: bool | None = None
        self._last_capture_used_portal = False
        self._cli_direct_save = False
        self._cli_save_path: str | None = None
        self._cli_upload = False
        self._quit_after_capture = False
        self._tool_group_buttons: dict[str, QToolButton] = {}

        self.setWindowTitle("ksnip")
        self.resize(1200, 800)
        self._apply_window_icon()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._handle_current_tab_changed)
        self.setCentralWidget(self.tabs)

        self.status_label = QLabel(self.tr("Ready"))
        self.statusBar().addPermanentWidget(self.status_label)

        self._build_actions()
        self._build_toolbar()
        self._build_menus()
        QGuiApplication.clipboard().dataChanged.connect(self._update_actions)
        self._restore_ui_settings()
        self._setup_tray_icon()
        self._apply_shortcuts()
        self._update_actions()
        self.new_tab()
        self._apply_tool_selection_from_settings()

    def _icon_base_path(self) -> Path:
        return Path(__file__).resolve().parent / "icons"

    def _use_light_icons(self) -> bool:
        window_color = self.palette().color(self.backgroundRole())
        return window_color.lightness() < 128

    def _load_icon(self, name: str) -> QIcon:
        base_path = self._icon_base_path()
        variant_order = ("light", "dark") if self._use_light_icons() else ("dark", "light")
        candidates = [base_path / f"{name}.svg"]
        for variant in variant_order:
            candidates.extend(
                [
                    base_path / variant / f"{name}.svg",
                    base_path / "kimageannotator" / variant / f"{name}.svg",
                ]
            )
        for candidate in candidates:
            if candidate.exists():
                return QIcon(str(candidate))
        return QIcon()

    def _load_first_icon(self, *names: str) -> QIcon:
        for name in names:
            icon = self._load_icon(name)
            if not icon.isNull():
                return icon
        return QIcon()

    def _themed_icon(self, theme_name: str, fallback_name: str) -> QIcon:
        """Load a desktop icon while keeping a packaged fallback for minimal WMs."""
        return QIcon.fromTheme(theme_name, self._load_icon(fallback_name))

    def _apply_window_icon(self) -> None:
        icon_path = self._icon_base_path() / "ksnip.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _default_sticker_paths(self) -> list[str]:
        stickers_dir = Path(__file__).resolve().parent / "stickers"
        if not stickers_dir.exists():
            return []
        return [str(path) for path in sorted(stickers_dir.glob("*.svg"))]

    def _configure_toolbar(
        self,
        toolbar: QToolBar,
        *,
        icon_size: int = 20,
        style: Qt.ToolButtonStyle = Qt.ToolButtonStyle.ToolButtonIconOnly,
    ) -> None:
        toolbar.setIconSize(QSize(icon_size, icon_size))
        toolbar.setToolButtonStyle(style)

    def _make_icon_label(self, icon_name: str, tooltip: str) -> QLabel:
        label = QLabel(self)
        icon = self._load_icon(icon_name)
        if not icon.isNull():
            label.setPixmap(icon.pixmap(16, 16))
        label.setToolTip(tooltip)
        return label

    def _make_tool_toggle(self, icon_name: str, tooltip: str, checked: bool, slot) -> QToolButton:
        button = QToolButton(self)
        button.setCheckable(True)
        button.setChecked(checked)
        button.setToolTip(tooltip)
        icon = self._load_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
        button.toggled.connect(slot)
        return button

    def _make_capture_menu_button(self) -> QToolButton:
        button = QToolButton(self)
        button.setText(self.tr("New"))
        button.setToolTip(self.tr("New Screenshot"))
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        icon = self._load_icon("drawRect")
        if not icon.isNull():
            button.setIcon(icon)

        menu = QMenu(button)
        menu.addAction(self.new_capture_rect_action)
        menu.addAction(self.new_capture_last_rect_action)
        menu.addAction(self.new_capture_full_action)
        menu.addAction(self.new_capture_current_action)
        menu.addAction(self.new_capture_active_action)
        menu.addAction(self.new_capture_under_cursor_action)
        menu.addAction(self.new_capture_portal_action)
        button.setMenu(menu)
        return button

    def _make_tool_action(self, icon_name: str, text: str, tool: Tool, group_name: str | None = None) -> QAction:
        action = QAction(self._load_icon(icon_name), text, self)
        action.setCheckable(True)
        if group_name is None:
            action.triggered.connect(lambda: self.set_tool(tool))
        else:
            action.triggered.connect(lambda: self._select_group_tool(group_name, action, tool))
        self.tool_action_group.addAction(action)
        return action

    def _make_image_effect_action(self, icon_name: str, text: str, effect: str) -> QAction:
        action = QAction(self._load_icon(icon_name), text, self)
        action.setCheckable(True)
        action.triggered.connect(lambda checked=False: checked and self.apply_image_effect(effect))
        self.image_effect_action_group.addAction(action)
        return action

    def _set_tool_group_default_action(self, group_name: str, action: QAction) -> None:
        button = self._tool_group_buttons.get(group_name)
        if button is not None:
            button.setDefaultAction(action)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    def _select_group_tool(self, group_name: str, action: QAction, tool: Tool) -> None:
        self._set_tool_group_default_action(group_name, action)
        self.set_tool(tool)

    def _make_tool_group_widget(self, group_name: str, main_action: QAction, menu_actions: list[QAction], *, enable_menu: bool = True) -> QWidget:
        host = QWidget(self)
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_button = QToolButton(host)
        main_button.setDefaultAction(main_action)
        main_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        main_button.setAutoRaise(False)
        main_button.setIconSize(QSize(24, 24))
        main_button.setFixedSize(30, 30)
        layout.addWidget(main_button)

        menu_button = QToolButton(host)
        menu_button.setArrowType(Qt.ArrowType.DownArrow)
        menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu_button.setAutoRaise(False)
        menu_button.setFixedSize(14, 30)
        menu_button.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0px; }")
        menu = QMenu(menu_button)
        for action in menu_actions:
            menu.addAction(action)
        menu_button.setMenu(menu)
        menu_button.setEnabled(enable_menu)
        layout.addWidget(menu_button)

        self._tool_group_buttons[group_name] = main_button
        return host

    def _make_action_button(self, action: QAction, parent: QWidget | None = None, *, enabled: bool = True) -> QToolButton:
        button = QToolButton(parent or self)
        button.setDefaultAction(action)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setAutoRaise(False)
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(30, 30)
        button.setEnabled(enabled)
        return button

    def _make_single_tool_widget(self, action: QAction, *, enabled: bool = True) -> QWidget:
        host = QWidget(self)
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._make_action_button(action, host, enabled=enabled))
        spacer = QWidget(host)
        spacer.setFixedSize(14, 30)
        layout.addWidget(spacer)
        return host

    def _make_property_group(self, *widgets: QWidget) -> QWidget:
        host = QWidget(self)
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for widget in widgets:
            layout.addWidget(widget)
        host.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        return host

    def _sync_toolbox_color_button(self, color: QColor | None = None) -> None:
        if not hasattr(self, "toolbox_color_button"):
            return
        resolved = color
        canvas = self.current_canvas()
        if resolved is None and canvas is not None and canvas.tool() == Tool.SELECT:
            selected_color = canvas.selected_item_color()
            if selected_color is not None:
                resolved = QColor(selected_color)
        if resolved is None:
            selected_color = canvas.selected_item_color() if canvas is not None else None
            resolved = QColor(selected_color) if selected_color is not None else QColor("#df5a17")
        self.toolbox_color_button.setStyleSheet(
            f"QToolButton {{ background: {resolved.name()}; border: 1px solid #666; min-width: 22px; min-height: 22px; max-width: 22px; max-height: 22px; }}"
        )
        if hasattr(self, "toolbox_color_palette"):
            self.toolbox_color_palette.select_color(resolved)

    def _sync_property_color_buttons(self) -> None:
        if not hasattr(self, "property_color_button"):
            return
        canvas = self.current_canvas()
        stroke = QColor("#df5a17")
        secondary = QColor("#ffffff")
        if canvas is not None:
            if canvas.tool() == Tool.SELECT:
                selected_color = canvas.selected_item_color()
                if selected_color is not None:
                    stroke = QColor(selected_color)
                else:
                    stroke = canvas.color()
                selected_text_color = canvas.selected_item_text_color()
                if selected_text_color is not None:
                    secondary = QColor(selected_text_color)
                else:
                    secondary = canvas.text_color()
            else:
                stroke = canvas.color()
                secondary = canvas.text_color()
            self.property_color_button.setStyleSheet(
                f"QToolButton {{ background: {stroke.name()}; border: 1px solid #666; min-width: 22px; min-height: 22px; max-width: 22px; max-height: 22px; }}"
            )
            if hasattr(self, "property_text_color_button"):
                self.property_text_color_button.setStyleSheet(
                    f"QToolButton {{ background: {secondary.name()}; border: 1px solid #666; min-width: 22px; min-height: 22px; max-width: 22px; max-height: 22px; }}"
                )
            if hasattr(self, "property_color_palette"):
                self.property_color_palette.select_color(stroke)
            if hasattr(self, "property_text_color_palette"):
                self.property_text_color_palette.select_color(secondary)

    def _fill_mode_icon_name(self, fill_mode: FillMode | None) -> str:
        if fill_mode == FillMode.BORDER_AND_NO_FILL:
            return "fillType_borderAndNoFill"
        if fill_mode == FillMode.NO_BORDER_AND_NO_FILL:
            return "fillType_noBorderAndNoFill"
        return "fillType_borderAndFill"

    def _sync_fill_mode_button(self) -> None:
        if not hasattr(self, "fill_mode_button"):
            return
        fill_mode = self.fill_mode.currentData()
        if fill_mode is None:
            fill_mode = FillMode.BORDER_AND_FILL
        self.fill_mode_button.setIcon(self._load_icon(self._fill_mode_icon_name(fill_mode)))

    def _current_fill_mode_value(self) -> FillMode:
        fill_mode = self.fill_mode.currentData() if hasattr(self, "fill_mode") else None
        return fill_mode if isinstance(fill_mode, FillMode) else FillMode.BORDER_AND_FILL

    def _fill_mode_options_for_tool(self, tool: Tool | None) -> list[tuple[str, FillMode]]:
        if tool in {Tool.TEXT, Tool.NUMBER, Tool.NUMBER_ARROW}:
            return [
                ("Border and Fill", FillMode.BORDER_AND_FILL),
                ("Border and No Fill", FillMode.BORDER_AND_NO_FILL),
                ("No Border and No Fill", FillMode.NO_BORDER_AND_NO_FILL),
            ]
        if tool in {Tool.TEXT_ARROW, Tool.RECT, Tool.ELLIPSE}:
            return [
                ("Border and Fill", FillMode.BORDER_AND_FILL),
                ("Border and No Fill", FillMode.BORDER_AND_NO_FILL),
            ]
        return []

    def _refresh_fill_mode_choices(self, tool: Tool | None) -> None:
        if not hasattr(self, "fill_mode"):
            return
        options = self._fill_mode_options_for_tool(tool)
        current_mode = self.fill_mode.currentData()
        self.fill_mode.blockSignals(True)
        self.fill_mode.clear()
        for label, mode in options:
            self.fill_mode.addItem(label, mode)
        if options:
            allowed_modes = [mode for _, mode in options]
            target_mode = current_mode if current_mode in allowed_modes else allowed_modes[0]
            self.fill_mode.setCurrentIndex(max(0, self.fill_mode.findData(target_mode)))
        self.fill_mode.blockSignals(False)
        self.fill_mode_button.setEnabled(len(options) > 1)
        self._sync_fill_mode_button()

    def _sync_auxiliary_property_controls(self) -> None:
        if not hasattr(self, "blur_strength"):
            return
        if self.blur_strength.value() != self.stroke_width.value():
            self.blur_strength.blockSignals(True)
            self.blur_strength.setValue(self.stroke_width.value())
            self.blur_strength.blockSignals(False)
        if hasattr(self, "shadow_state_button"):
            self.shadow_state_button.setIcon(self._load_icon("check" if self.shadow_state_button.isChecked() else "disabled"))
        if hasattr(self, "sticker_picker_button"):
            self._sync_sticker_button()

    def _cycle_fill_mode(self) -> None:
        if self.fill_mode.count() == 0:
            return
        next_index = (self.fill_mode.currentIndex() + 1) % self.fill_mode.count()
        self.fill_mode.setCurrentIndex(next_index)

    def _open_sticker_picker(self) -> None:
        canvas = self.current_canvas()
        current_path = None
        if canvas is not None:
            current_path = canvas.selected_item_sticker_path() or canvas.sticker_path()
        dialog = StickerPickerDialog(self, settings=self._settings, current_path=current_path)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_path():
            self._select_sticker(dialog.selected_path())

    def _sync_sticker_button(self) -> None:
        canvas = self.current_canvas()
        sticker_path = canvas.selected_item_sticker_path() if canvas is not None else None
        if not sticker_path and canvas is not None:
            sticker_path = canvas.sticker_path()
        if not sticker_path:
            paths = self._default_sticker_paths()
            sticker_path = paths[0] if paths else None
        if sticker_path:
            self.sticker_picker_button.setIcon(QIcon(sticker_path))

    def _select_sticker(self, sticker_path: str) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_sticker_to_selected_item(sticker_path):
            self.status_label.setText(self.tr("Updated selected sticker"))
        else:
            canvas.set_sticker_path(sticker_path)
        self._sync_sticker_button()

    def _effective_property_tool(self) -> Tool | None:
        canvas = self.current_canvas()
        if canvas is None:
            return None
        tool = canvas.tool()
        if tool == Tool.SELECT and canvas.has_selected_item():
            selected_kind = canvas.selected_item_kind()
            if selected_kind is not None:
                return selected_kind
        return tool

    def _update_property_toolbar_for_tool(self) -> None:
        if not hasattr(self, "_property_groups") or not hasattr(self, "properties_toolbar"):
            return
        tool = self._effective_property_tool()
        if tool is None:
            tool = Tool.SELECT
        self._refresh_fill_mode_choices(tool)
        show_stroke = tool in {
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.LINE,
            Tool.PEN,
            Tool.MARKER_PEN,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.MARKER_RECT,
            Tool.MARKER_ELLIPSE,
        }
        show_width = tool in {
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.LINE,
            Tool.PEN,
            Tool.MARKER_PEN,
            Tool.TEXT,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
        }
        show_text_color = tool in {
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
        }
        show_fill_mode = tool in {
            Tool.TEXT,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
        }
        show_opacity = tool in {
            Tool.DUPLICATE,
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.LINE,
            Tool.PEN,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.IMAGE,
            Tool.STICKER,
        }
        show_font = tool in {
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
        }
        show_style = show_font
        show_number = tool in {Tool.NUMBER, Tool.NUMBER_POINTER, Tool.NUMBER_ARROW}
        show_blur = tool in {Tool.BLUR, Tool.PIXELATE}
        show_shadow = tool in {
            Tool.ARROW,
            Tool.DOUBLE_ARROW,
            Tool.LINE,
            Tool.PEN,
            Tool.TEXT,
            Tool.TEXT_POINTER,
            Tool.TEXT_ARROW,
            Tool.NUMBER,
            Tool.NUMBER_POINTER,
            Tool.NUMBER_ARROW,
            Tool.RECT,
            Tool.ELLIPSE,
            Tool.IMAGE,
            Tool.STICKER,
        }
        show_scaling = tool == Tool.STICKER
        show_sticker = tool == Tool.STICKER
        visibility = {
            "stroke": show_stroke,
            "width": show_width,
            "text_color": show_text_color,
            "fill_mode": show_fill_mode,
            "font": show_font,
            "style": show_style,
            "number": show_number,
            "blur": show_blur,
            "sticker": show_sticker,
            "shadow": show_shadow,
            "scaling": show_scaling,
            "opacity": show_opacity,
        }
        # KImageAnnotator keeps the Item Settings row and its drag handle
        # visible even when Selection has no configurable item.
        visibility["handle"] = True

        if tool == Tool.MARKER_PEN:
            self.stroke_width.setMaximum(100)
        else:
            self.stroke_width.setMaximum(20 if tool not in {Tool.BLUR, Tool.PIXELATE} else 60)

        show_alpha = tool not in {Tool.MARKER_PEN, Tool.MARKER_RECT, Tool.MARKER_ELLIPSE}
        if hasattr(self, "property_color_palette"):
            self.property_color_palette.set_show_alpha(show_alpha)
        if hasattr(self, "toolbox_color_palette"):
            self.toolbox_color_palette.set_show_alpha(show_alpha)

        self._render_property_toolbar(visibility)

    def _render_property_toolbar(self, visibility: dict[str, bool]) -> None:
        self.properties_toolbar.clear()
        first_visible = True
        for name, widget in self._property_order:
            widget.setVisible(visibility.get(name, False))
            if visibility.get(name, False):
                if not first_visible:
                    self.properties_toolbar.addSeparator()
                self.properties_toolbar.addWidget(widget)
                first_visible = False
        self._property_toolbar_has_controls = not first_visible
        self.properties_toolbar.setVisible(self._property_toolbar_has_controls and not self._docks_collapsed)

    def _build_actions(self) -> None:
        self.tool_action_group = QActionGroup(self)
        self.tool_action_group.setExclusive(True)

        self.new_capture_rect_action = QAction(self._load_icon("drawRect"), self.tr("Rect Area"), self)
        self.new_capture_rect_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_rect_action.triggered.connect(self.capture_rect_area)
        self.new_capture_last_rect_action = QAction(self._load_icon("lastRect"), self.tr("Last Rect Area"), self)
        self.new_capture_last_rect_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_last_rect_action.triggered.connect(self.capture_last_rect_area)
        self.new_capture_full_action = QAction(self._load_icon("fullScreen"), self.tr("Full Screen"), self)
        self.new_capture_full_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_full_action.triggered.connect(self.capture_fullscreen)
        self.new_capture_current_action = QAction(self._load_icon("currentScreen"), self.tr("Current Screen"), self)
        self.new_capture_current_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_current_action.triggered.connect(self.capture_current_screen)
        self.new_capture_active_action = QAction(self._load_icon("activeWindow"), self.tr("Active Window"), self)
        self.new_capture_active_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_active_action.triggered.connect(self.capture_active_window)
        self.new_capture_under_cursor_action = QAction(self._load_icon("windowUnderCursor"), self.tr("Window Under Cursor"), self)
        self.new_capture_under_cursor_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_under_cursor_action.triggered.connect(self.capture_window_under_cursor)
        self.new_capture_portal_action = QAction(self._load_icon("wayland"), self.tr("Portal"), self)
        self.new_capture_portal_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.new_capture_portal_action.triggered.connect(self.capture_portal)

        self.open_action = QAction(self.style().standardIcon(self.style().StandardPixmap.SP_DialogOpenButton), self.tr("Open"), self)
        self.open_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_image)

        self.save_action = QAction(self._load_icon("save"), self.tr("Save"), self)
        self.save_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_image)

        self.save_as_action = QAction(self._load_icon("saveAs"), self.tr("Save As..."), self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_image_as)

        self.save_all_action = QAction(self._load_icon("save"), self.tr("Save All"), self)
        self.save_all_action.triggered.connect(self.save_all_images)

        self.print_action = QAction(QIcon.fromTheme("document-print"), self.tr("Print"), self)
        self.print_action.setShortcut(QKeySequence.StandardKey.Print)
        self.print_action.triggered.connect(self.print_current_image)

        self.print_preview_action = QAction(QIcon.fromTheme("document-print-preview"), self.tr("Print Preview"), self)
        self.print_preview_action.triggered.connect(self.preview_current_image)

        self.copy_action = QAction(self._load_icon("copy"), self.tr("Copy"), self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.copy_image)

        self.copy_data_uri_action = QAction(self._themed_icon("edit-copy", "copy"), self.tr("Copy as data URI"), self)
        self.copy_data_uri_action.triggered.connect(self.copy_image_as_data_uri)

        self.copy_path_action = QAction(self._themed_icon("edit-copy", "copy"), self.tr("Copy Path"), self)
        self.copy_path_action.triggered.connect(self.copy_image_path)

        self.rename_action = QAction(self._themed_icon("edit-rename", "text"), self.tr("Rename"), self)
        self.rename_action.setShortcut("F2")
        self.rename_action.triggered.connect(self.rename_current_image)

        self.delete_image_action = QAction(self._load_icon("delete"), self.tr("Delete Image..."), self)
        self.delete_image_action.triggered.connect(self.delete_current_image_file)

        self.open_directory_action = QAction(self._themed_icon("folder-open", "action"), self.tr("Open Directory"), self)
        self.open_directory_action.triggered.connect(self.open_image_directory)

        self.copy_item_action = QAction(self._themed_icon("edit-copy", "copy"), self.tr("Copy Item"), self)
        self.copy_item_action.setShortcut("Ctrl+Shift+C")
        self.copy_item_action.triggered.connect(self.copy_selected_item)

        self.close_tab_action = QAction(self._themed_icon("window-close", "delete"), self.tr("Close Tab"), self)
        self.close_tab_action.setShortcut(QKeySequence.StandardKey.Close)
        self.close_tab_action.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))

        self.pen_action = QAction(self._load_first_icon("pen", "markerPen"), self.tr("Pen"), self)
        self.pen_action.setCheckable(True)
        self.pen_action.triggered.connect(lambda: self.set_tool(Tool.PEN))
        self.tool_action_group.addAction(self.pen_action)

        self.marker_pen_action = self._make_tool_action("markerPen", self.tr("Marker Pen"), Tool.MARKER_PEN, "marker")

        self.line_action = QAction(self._load_icon("line"), self.tr("Line"), self)
        self.line_action.setCheckable(True)
        self.line_action.triggered.connect(lambda: self.set_tool(Tool.LINE))
        self.tool_action_group.addAction(self.line_action)

        self.arrow_action = QAction(self._load_icon("arrow"), self.tr("Arrow"), self)
        self.arrow_action.setCheckable(True)
        self.arrow_action.triggered.connect(lambda: self._select_group_tool("arrow", self.arrow_action, Tool.ARROW))
        self.tool_action_group.addAction(self.arrow_action)

        self.double_arrow_action = self._make_tool_action("doubleArrow", self.tr("Double Arrow"), Tool.DOUBLE_ARROW, "arrow")

        self.rect_action = QAction(self._load_icon("rect"), self.tr("Rectangle"), self)
        self.rect_action.setCheckable(True)
        self.rect_action.triggered.connect(lambda: self._select_group_tool("shape", self.rect_action, Tool.RECT))
        self.tool_action_group.addAction(self.rect_action)

        self.ellipse_action = QAction(self._load_icon("ellipse"), self.tr("Ellipse"), self)
        self.ellipse_action.setCheckable(True)
        self.ellipse_action.triggered.connect(lambda: self._select_group_tool("shape", self.ellipse_action, Tool.ELLIPSE))
        self.tool_action_group.addAction(self.ellipse_action)

        self.text_action = QAction(self._load_icon("text"), self.tr("Text"), self)
        self.text_action.setCheckable(True)
        self.text_action.triggered.connect(lambda: self._select_group_tool("text", self.text_action, Tool.TEXT))
        self.tool_action_group.addAction(self.text_action)

        self.text_pointer_action = self._make_tool_action("textPointer", self.tr("Text Pointer"), Tool.TEXT_POINTER, "text")
        self.text_arrow_action = self._make_tool_action("textArrow", self.tr("Text Arrow"), Tool.TEXT_ARROW, "text")

        self.blur_action = QAction(self._load_icon("blur"), self.tr("Blur"), self)
        self.blur_action.setCheckable(True)
        self.blur_action.triggered.connect(lambda: self._select_group_tool("effect", self.blur_action, Tool.BLUR))
        self.tool_action_group.addAction(self.blur_action)

        self.pixelate_action = QAction(self._load_icon("pixelate"), self.tr("Pixelate"), self)
        self.pixelate_action.setCheckable(True)
        self.pixelate_action.triggered.connect(lambda: self._select_group_tool("effect", self.pixelate_action, Tool.PIXELATE))
        self.tool_action_group.addAction(self.pixelate_action)

        self.crop_action = QAction(self._load_icon("crop"), self.tr("Crop"), self)
        self.crop_action.setCheckable(True)
        self.crop_action.triggered.connect(lambda: self.set_tool(Tool.CROP))
        self.tool_action_group.addAction(self.crop_action)

        self.cut_action = QAction(self._load_icon("cut"), self.tr("Cut"), self)
        self.cut_action.triggered.connect(self.cut_image)

        self.select_action = QAction(self._load_icon("select"), self.tr("Select"), self)
        self.select_action.setCheckable(True)
        self.select_action.triggered.connect(lambda: self.set_tool(Tool.SELECT))
        self.tool_action_group.addAction(self.select_action)

        self.duplicate_tool_action = self._make_tool_action("duplicate", self.tr("Duplicate"), Tool.DUPLICATE)
        self.duplicate_tool_action.setShortcut("U")

        self.marker_rect_action = self._make_tool_action("markerRect", self.tr("Marker Rectangle"), Tool.MARKER_RECT, "marker")
        self.marker_ellipse_action = self._make_tool_action("markerEllipse", self.tr("Marker Ellipse"), Tool.MARKER_ELLIPSE, "marker")
        self.number_action = self._make_tool_action("number", self.tr("Number"), Tool.NUMBER, "number")
        self.number_pointer_action = self._make_tool_action("numberPointer", self.tr("Number Pointer"), Tool.NUMBER_POINTER, "number")
        self.number_arrow_action = self._make_tool_action("numberArrow", self.tr("Number Arrow"), Tool.NUMBER_ARROW, "number")
        self.sticker_action = QAction(self._load_icon("sticker"), self.tr("Sticker"), self)
        self.sticker_action.setCheckable(True)
        self.sticker_action.triggered.connect(lambda: self.set_tool(Tool.STICKER))
        self.tool_action_group.addAction(self.sticker_action)

        self.color_action = QAction(self._load_icon("color"), self.tr("Color"), self)
        self.color_action.triggered.connect(self.select_color)

        self.undo_action = QAction(self._load_icon("undo"), self.tr("Undo"), self)
        self.undo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)

        self.redo_action = QAction(self._load_icon("redo"), self.tr("Redo"), self)
        self.redo_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)

        self.paste_action = QAction(self._load_icon("paste"), self.tr("Paste"), self)
        self.paste_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.paste_image)

        self.paste_embedded_action = QAction(self._load_icon("pasteEmbedded"), self.tr("Paste Embedded"), self)
        self.paste_embedded_action.setShortcut("Ctrl+Shift+V")
        self.paste_embedded_action.triggered.connect(self.paste_embedded_image)

        self.paste_item_action = QAction(self._themed_icon("edit-paste", "paste"), self.tr("Paste Item"), self)
        self.paste_item_action.setShortcut("Ctrl+Alt+V")
        self.paste_item_action.triggered.connect(self.paste_item)

        self.delete_action = QAction(self._load_icon("delete"), self.tr("Delete Item"), self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_selected_item)

        self.duplicate_action = QAction(self._load_icon("duplicate"), self.tr("Duplicate Item"), self)
        self.duplicate_action.setShortcut("Ctrl+D")
        self.duplicate_action.triggered.connect(self.duplicate_selected_item)

        self.edit_text_action = QAction(self._themed_icon("document-edit", "text"), self.tr("Edit Text..."), self)
        self.edit_text_action.triggered.connect(self.edit_selected_text)

        self.bring_to_front_action = QAction(self._themed_icon("object-raise", "action"), self.tr("Bring To Front"), self)
        self.bring_to_front_action.triggered.connect(self.bring_selected_item_to_front)

        self.send_to_back_action = QAction(self._themed_icon("object-lower", "action"), self.tr("Send To Back"), self)
        self.send_to_back_action.triggered.connect(self.send_selected_item_to_back)

        self.rotate_action = QAction(self._load_icon("rotate"), self.tr("Rotate"), self)
        self.rotate_action.triggered.connect(self.rotate_image)

        self.scale_action = QAction(self._load_icon("scale"), self.tr("Scale"), self)
        self.scale_action.triggered.connect(self.scale_image)

        self.image_effect_action_group = QActionGroup(self)
        self.image_effect_action_group.setExclusive(True)
        self.no_effect_action = self._make_image_effect_action("disabled", self.tr("No Effect"), "none")
        self.drop_shadow_effect_action = self._make_image_effect_action("dropShadow", self.tr("Drop Shadow"), "drop_shadow")
        self.grayscale_action = self._make_image_effect_action("grayscale", self.tr("Grayscale"), "grayscale")
        self.invert_color_action = self._make_image_effect_action("invertColor", self.tr("Invert Color"), "invert")
        self.border_effect_action = self._make_image_effect_action("border", self.tr("Border"), "border")
        self.no_effect_action.setChecked(True)

        self.modify_canvas_action = QAction(self._load_icon("modifycanvas"), self.tr("Modify Canvas..."), self)
        self.modify_canvas_action.triggered.connect(self.modify_canvas)

        self.toggle_docks_action = QAction(self._themed_icon("view-restore", "action"), self.tr("Hide Docks"), self)
        self.toggle_docks_action.setShortcut("Tab")
        self.toggle_docks_action.triggered.connect(self.toggle_docks)

        self.pin_action = QAction(self._load_icon("pin"), self.tr("Pin"), self)
        self.pin_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.pin_action.triggered.connect(self.pin_image)

        self.add_watermark_action = QAction(self._themed_icon("insert-image", "pasteEmbedded"), self.tr("Add Watermark"), self)
        self.add_watermark_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.add_watermark_action.setShortcut("Shift+W")
        self.add_watermark_action.triggered.connect(self.add_watermark)

        self.upload_action = QAction(self._themed_icon("network-transmit", "action"), self.tr("Upload"), self)
        self.upload_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.upload_action.triggered.connect(self.upload_image)

        self.ocr_action = QAction(self._themed_icon("edit-find", "text"), self.tr("OCR Text Recognition"), self)
        self.ocr_action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.ocr_action.triggered.connect(self.run_ocr)

        self.update_watermark_action = QAction(self._themed_icon("document-open", "pasteEmbedded"), self.tr("Update Watermark Image..."), self)
        self.update_watermark_action.triggered.connect(self.update_watermark_image)

        self.rotate_watermark_action = QAction(self._load_icon("rotate"), self.tr("Rotate Watermark"), self)
        self.rotate_watermark_action.setCheckable(True)
        self.rotate_watermark_action.setChecked(self._setting_bool("watermark/rotate", True))
        self.rotate_watermark_action.toggled.connect(self._set_rotate_watermark)

        self.settings_action = QAction(self._themed_icon("preferences-system", "action"), self.tr("Settings"), self)
        self.settings_action.triggered.connect(self.open_settings_dialog)

        self.about_action = QAction(self._themed_icon("help-about", "ksnip"), self.tr("About"), self)
        self.about_action.triggered.connect(self.show_about)

        self.clear_recent_images_action = QAction(self._themed_icon("edit-clear-history", "delete"), self.tr("Clear Recent Images"), self)
        self.clear_recent_images_action.triggered.connect(self.clear_recent_images)

        self.quit_action = QAction(self.style().standardIcon(self.style().StandardPixmap.SP_DialogCloseButton), self.tr("Quit"), self)
        self.quit_action.triggered.connect(self.quit_application)

        self.zoom_out_action = QAction(self._themed_icon("zoom-out", "zoom"), self.tr("Zoom Out"), self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.triggered.connect(self.zoom_out_current_canvas)
        self.zoom_reset_action = QAction(self._load_icon("resetZoom"), self.tr("Reset Zoom"), self)
        self.zoom_reset_action.setShortcut(QKeySequence("Ctrl+0"))
        self.zoom_reset_action.triggered.connect(self.reset_zoom_current_canvas)
        self.zoom_in_action = QAction(self._themed_icon("zoom-in", "zoom"), self.tr("Zoom In"), self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.triggered.connect(self.zoom_in_current_canvas)
        self.zoom_fit_action = QAction(self._load_icon("fitImage"), self.tr("Fit Image"), self)
        self.zoom_fit_action.setShortcut(QKeySequence("Ctrl+F"))
        self.zoom_fit_action.triggered.connect(self.fit_current_canvas)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self._configure_toolbar(toolbar, icon_size=20, style=Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.main_toolbar = toolbar

        self.capture_menu_button = self._make_capture_menu_button()
        toolbar.addWidget(self.capture_menu_button)
        toolbar.addSeparator()
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.copy_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addAction(self.crop_action)
        toolbar.addAction(self.cut_action)
        toolbar.addSeparator()
        toolbar.addWidget(self._make_icon_label("clock", self.tr("Capture delay")))

        self.capture_delay_toolbar = QSpinBox(self)
        self.capture_delay_toolbar.setRange(0, 60)
        self.capture_delay_toolbar.setSuffix("s")
        self.capture_delay_toolbar.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.capture_delay_toolbar.setFixedWidth(68)
        self.capture_delay_toolbar.setValue(self._setting_int("capture/delay_seconds", 0))
        self.capture_delay_toolbar.valueChanged.connect(self._apply_capture_delay)
        toolbar.addWidget(self.capture_delay_toolbar)

        properties_toolbar = QToolBar("Properties", self)
        properties_toolbar.setMovable(False)
        self._configure_toolbar(properties_toolbar, icon_size=16, style=Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBarBreak(Qt.ToolBarArea.TopToolBarArea)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, properties_toolbar)
        self.properties_toolbar = properties_toolbar

        self.property_handle_group = self._make_property_group(QLabel("::", self))

        self.property_color_button = QToolButton(self)
        self.property_color_button.setToolTip(self.tr("Stroke color"))
        self.property_color_button.setFixedSize(22, 22)
        self.property_color_palette = ColorPaletteMenu(parent=self.property_color_button)
        self.property_color_palette.color_selected.connect(self._apply_selected_color)
        self.property_color_button.setMenu(self.property_color_palette)
        self.property_color_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.property_stroke_group = self._make_property_group(
            self._make_icon_label("color", self.tr("Stroke color")),
            self.property_color_button,
        )

        self.stroke_width = QSpinBox()
        self.stroke_width.setRange(1, 60)
        self.stroke_width.setValue(3)
        self.stroke_width.setFixedWidth(52)
        self.stroke_width.setFixedHeight(22)
        self.stroke_width.valueChanged.connect(self._apply_stroke_width)
        self.property_width_group = self._make_property_group(self._make_icon_label("width", self.tr("Stroke width")), self.stroke_width)

        self.fill_mode = QComboBox()
        self.fill_mode.hide()
        self.fill_mode.currentIndexChanged.connect(self._apply_fill_mode)
        self.fill_mode_button = QToolButton(self)
        self.fill_mode_button.setToolTip(self.tr("Fill mode"))
        self.fill_mode_button.setFixedSize(22, 22)
        self.fill_mode_button.clicked.connect(self._cycle_fill_mode)
        self.property_fill_mode_group = self._make_property_group(
            self._make_icon_label("fillType_borderAndFill", self.tr("Fill mode")),
            self.fill_mode_button,
        )

        self.property_text_color_button = QToolButton(self)
        self.property_text_color_button.setToolTip(self.tr("Text color"))
        self.property_text_color_button.setFixedSize(22, 22)
        self.property_text_color_palette = ColorPaletteMenu(parent=self.property_text_color_button)
        self.property_text_color_palette.color_selected.connect(self._apply_selected_text_color)
        self.property_text_color_button.setMenu(self.property_text_color_palette)
        self.property_text_color_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.property_text_color_group = self._make_property_group(
            self._make_icon_label("textColor", self.tr("Text color")),
            self.property_text_color_button,
        )

        self.font_family = QFontComboBox()
        self.font_family.setMaximumWidth(132)
        self.font_family.setFixedHeight(22)
        self.font_family.currentFontChanged.connect(self._apply_font_family)

        self.font_size = QSpinBox()
        self.font_size.setRange(6, 144)
        self.font_size.setValue(14)
        self.font_size.setFixedWidth(52)
        self.font_size.setFixedHeight(22)
        self.font_size.valueChanged.connect(self._apply_font_size)
        self.property_font_group = self._make_property_group(
            self._make_icon_label("text", self.tr("Font")),
            self.font_family,
            self.font_size,
        )

        self.bold_button = self._make_tool_toggle("bold", self.tr("Bold"), False, self._apply_bold)
        self.italic_button = self._make_tool_toggle("italic", self.tr("Italic"), False, self._apply_italic)
        self.underline_button = self._make_tool_toggle("underline", self.tr("Underline"), False, self._apply_underline)
        self.bold_button.setFixedSize(22, 22)
        self.italic_button.setFixedSize(22, 22)
        self.underline_button.setFixedSize(22, 22)
        self.property_style_group = self._make_property_group(self.bold_button, self.italic_button, self.underline_button)

        self.number_value = QSpinBox()
        self.number_value.setRange(1, 999)
        self.number_value.setValue(1)
        self.number_value.setFixedWidth(48)
        self.number_value.setFixedHeight(22)
        self.number_value.valueChanged.connect(self._apply_number_value)
        self.property_number_group = self._make_property_group(self._make_icon_label("number", self.tr("Number")), self.number_value)

        self.blur_strength = QSpinBox()
        self.blur_strength.setRange(1, 60)
        self.blur_strength.setValue(10)
        self.blur_strength.setFixedWidth(52)
        self.blur_strength.setFixedHeight(22)
        self.blur_strength.valueChanged.connect(self._apply_blur_strength)
        self.property_blur_group = self._make_property_group(self._make_icon_label("obfuscateFactor", self.tr("Effect strength")), self.blur_strength)

        self.sticker_picker_button = QToolButton(self)
        self.sticker_picker_button.setIcon(self._load_icon("sticker"))
        self.sticker_picker_button.setToolTip(self.tr("Select Sticker"))
        self.sticker_picker_button.setFixedSize(22, 22)
        self.sticker_picker_button.clicked.connect(self._open_sticker_picker)
        self.property_sticker_group = self._make_property_group(self._make_icon_label("sticker", self.tr("Sticker")), self.sticker_picker_button)

        self.shadow_state_button = QToolButton(self)
        self.shadow_state_button.setCheckable(True)
        self.shadow_state_button.setChecked(self._setting_bool("editor/shadow_enabled", True))
        self.shadow_state_button.setFixedSize(22, 22)
        self.shadow_state_button.setToolTip(self.tr("Item shadow"))
        self.shadow_state_button.toggled.connect(self._apply_shadow_enabled)
        self.property_shadow_group = self._make_property_group(self._make_icon_label("dropShadow", self.tr("Item shadow")), self.shadow_state_button)

        self.scaling = QSpinBox()
        self.scaling.setRange(0, 500)
        self.scaling.setValue(self._setting_int("editor/scaling_percent", 100))
        self.scaling.setSuffix("%")
        self.scaling.setSingleStep(10)
        self.scaling.setFixedWidth(62)
        self.scaling.setFixedHeight(22)
        self.scaling.valueChanged.connect(self._apply_scaling)
        self.property_scaling_group = self._make_property_group(self._make_icon_label("scale", self.tr("Scale")), self.scaling)

        self.opacity = QSpinBox()
        self.opacity.setRange(0, 100)
        self.opacity.setValue(100)
        self.opacity.setSuffix("%")
        self.opacity.setFixedWidth(62)
        self.opacity.setFixedHeight(22)
        self.opacity.valueChanged.connect(self._apply_opacity)
        self.property_opacity_group = self._make_property_group(self._make_icon_label("opacity", self.tr("Opacity")), self.opacity)
        self._property_order = [
            ("handle", self.property_handle_group),
            ("stroke", self.property_stroke_group),
            ("width", self.property_width_group),
            ("fill_mode", self.property_fill_mode_group),
            ("text_color", self.property_text_color_group),
            ("font", self.property_font_group),
            ("style", self.property_style_group),
            ("number", self.property_number_group),
            ("blur", self.property_blur_group),
            ("sticker", self.property_sticker_group),
            ("shadow", self.property_shadow_group),
            ("scaling", self.property_scaling_group),
            ("opacity", self.property_opacity_group),
        ]
        self._property_groups = {
            "handle": self.property_handle_group,
            "stroke": self.property_stroke_group,
            "width": self.property_width_group,
            "fill_mode": self.property_fill_mode_group,
            "text_color": self.property_text_color_group,
            "font": self.property_font_group,
            "style": self.property_style_group,
            "number": self.property_number_group,
            "blur": self.property_blur_group,
            "sticker": self.property_sticker_group,
            "shadow": self.property_shadow_group,
            "scaling": self.property_scaling_group,
            "opacity": self.property_opacity_group,
        }
        self._sync_property_color_buttons()
        self._sync_fill_mode_button()
        self._sync_auxiliary_property_controls()
        self._update_property_toolbar_for_tool()

        self.left_toolbar = QToolBar("Tools", self)
        self.left_toolbar.setMovable(False)
        self.left_toolbar.setOrientation(Qt.Orientation.Vertical)
        self._configure_toolbar(self.left_toolbar, icon_size=24, style=Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.left_toolbar)
        toolbox_host = QWidget(self)
        toolbox_layout = QVBoxLayout(toolbox_host)
        toolbox_layout.setContentsMargins(4, 4, 4, 4)
        toolbox_layout.setSpacing(4)

        # Keep the synchronized palette object for programmatic color changes,
        # but do not render the old duplicate header above the vertical tools.
        self.toolbox_color_button = QToolButton(toolbox_host)
        self.toolbox_color_button.setToolTip(self.tr("Stroke color"))
        self.toolbox_color_palette = ColorPaletteMenu(parent=self.toolbox_color_button)
        self.toolbox_color_palette.color_selected.connect(self._apply_selected_color)
        self.toolbox_color_button.setMenu(self.toolbox_color_palette)
        self.toolbox_color_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.toolbox_color_button.setFixedSize(24, 24)

        tools_panel = QWidget(toolbox_host)
        tools_layout = QVBoxLayout(tools_panel)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(4)
        tools_layout.addWidget(self._make_single_tool_widget(self.select_action))
        tools_layout.addWidget(self._make_single_tool_widget(self.duplicate_tool_action))
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "arrow",
                self.arrow_action,
                [self.arrow_action, self.double_arrow_action, self.line_action],
            )
        )
        tools_layout.addWidget(self._make_single_tool_widget(self.pen_action))
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "marker",
                self.marker_pen_action,
                [self.marker_pen_action, self.marker_rect_action, self.marker_ellipse_action],
            )
        )
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "text",
                self.text_action,
                [self.text_action, self.text_pointer_action, self.text_arrow_action],
            )
        )
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "number",
                self.number_action,
                [self.number_action, self.number_pointer_action, self.number_arrow_action],
            )
        )
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "effect",
                self.blur_action,
                [self.blur_action, self.pixelate_action],
            )
        )
        tools_layout.addWidget(
            self._make_tool_group_widget(
                "shape",
                self.rect_action,
                [self.rect_action, self.ellipse_action],
            )
        )
        tools_layout.addWidget(self._make_single_tool_widget(self.sticker_action))
        tools_layout.addStretch(1)
        toolbox_layout.addWidget(tools_panel)
        toolbox_layout.addStretch(1)
        self.left_toolbar.addWidget(toolbox_host)
        self._sync_toolbox_color_button(QColor("#df5a17"))

        self.zoom_out_button = QToolButton(self)
        self.zoom_out_button.setText("-")
        self.zoom_out_button.setToolTip(self.tr("Zoom Out (%1)").replace("%1", self.zoom_out_action.shortcut().toString()))
        self.zoom_out_button.setFixedSize(22, 22)
        self.zoom_out_button.clicked.connect(self.zoom_out_current_canvas)
        self.zoom_out_button.hide()

        self.zoom_reset_button = QToolButton(self)
        self.zoom_reset_button.setDefaultAction(self.zoom_reset_action)
        self.zoom_reset_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.zoom_reset_button.setFixedSize(22, 22)

        self.zoom_fit_button = QToolButton(self)
        self.zoom_fit_button.setDefaultAction(self.zoom_fit_action)
        self.zoom_fit_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.zoom_fit_button.setFixedSize(22, 22)

        self.zoom_in_button = QToolButton(self)
        self.zoom_in_button.setText("+")
        self.zoom_in_button.setToolTip(self.tr("Zoom In (%1)").replace("%1", self.zoom_in_action.shortcut().toString()))
        self.zoom_in_button.setFixedSize(22, 22)
        self.zoom_in_button.clicked.connect(self.zoom_in_current_canvas)
        self.zoom_in_button.hide()

        self.zoom_spinbox = QSpinBox(self)
        self.zoom_spinbox.setRange(10, 800)
        self.zoom_spinbox.setSingleStep(10)
        self.zoom_spinbox.setSuffix("%")
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.zoom_spinbox.setFixedWidth(72)
        self.zoom_spinbox.setFixedHeight(22)
        self.zoom_spinbox.valueChanged.connect(self.set_current_canvas_zoom)

        # Ksnip keeps its compact zoom controls on the left of the bottom bar.
        # Normal status-bar widgets occupy that side; permanent widgets (such as
        # the status message) remain right-aligned.
        zoom_controls = QWidget(self)
        zoom_layout = QHBoxLayout(zoom_controls)
        zoom_layout.setContentsMargins(2, 0, 0, 0)
        zoom_layout.setSpacing(3)
        zoom_layout.addWidget(self._make_icon_label("zoom", self.tr("Zoom")))
        zoom_layout.addWidget(self.zoom_spinbox)
        zoom_layout.addWidget(self.zoom_fit_button)
        zoom_layout.addWidget(self.zoom_reset_button)
        self.statusBar().addWidget(zoom_controls)

        # The original annotator exposes Modify Canvas and Image Effect as
        # compact controls at the right edge of its bottom bar.
        bottom_tools = QWidget(self)
        bottom_tools_layout = QHBoxLayout(bottom_tools)
        bottom_tools_layout.setContentsMargins(2, 0, 2, 0)
        bottom_tools_layout.setSpacing(3)
        bottom_tools_layout.addWidget(QLabel("⋮", bottom_tools))

        self.bottom_modify_canvas_button = QToolButton(bottom_tools)
        self.bottom_modify_canvas_button.setDefaultAction(self.modify_canvas_action)
        self.bottom_modify_canvas_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.bottom_modify_canvas_button.setFixedSize(22, 22)
        bottom_tools_layout.addWidget(self.bottom_modify_canvas_button)

        self.bottom_effect_button = QToolButton(bottom_tools)
        self.bottom_effect_button.setIcon(self.no_effect_action.icon())
        self.bottom_effect_button.setToolTip(self.tr("Image Effect: %1").replace("%1", self.no_effect_action.text()))
        self.bottom_effect_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.bottom_effect_button.setFixedSize(22, 22)
        bottom_effect_menu = QMenu(self.bottom_effect_button)
        bottom_effect_menu.addAction(self.no_effect_action)
        bottom_effect_menu.addAction(self.drop_shadow_effect_action)
        bottom_effect_menu.addSeparator()
        bottom_effect_menu.addAction(self.grayscale_action)
        bottom_effect_menu.addAction(self.invert_color_action)
        bottom_effect_menu.addAction(self.border_effect_action)
        bottom_effect_menu.triggered.connect(self._sync_bottom_effect_button)
        self.bottom_effect_button.setMenu(bottom_effect_menu)
        bottom_tools_layout.addWidget(self.bottom_effect_button)
        self.statusBar().addPermanentWidget(bottom_tools)

        self.bold = self.bold_button
        self.italic = self.italic_button
        self.select_action.setChecked(True)
        self._set_tool_group_default_action("arrow", self.arrow_action)
        self._set_tool_group_default_action("marker", self.marker_pen_action)
        self._set_tool_group_default_action("text", self.text_action)
        self._set_tool_group_default_action("number", self.number_action)
        self._set_tool_group_default_action("effect", self.blur_action)
        self._set_tool_group_default_action("shape", self.rect_action)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("&File"))
        self.file_menu = file_menu
        new_capture_menu = file_menu.addMenu(self._load_icon("drawRect"), self.tr("New Screenshot"))
        new_capture_menu.addAction(self.new_capture_rect_action)
        new_capture_menu.addAction(self.new_capture_last_rect_action)
        new_capture_menu.addAction(self.new_capture_full_action)
        new_capture_menu.addAction(self.new_capture_current_action)
        new_capture_menu.addAction(self.new_capture_active_action)
        new_capture_menu.addAction(self.new_capture_under_cursor_action)
        new_capture_menu.addAction(self.new_capture_portal_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_action)
        self.recent_images_menu = file_menu.addMenu(self.tr("Recent Images"))
        self.recent_images_menu.aboutToShow.connect(self._populate_recent_images_menu)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addAction(self.save_all_action)
        file_menu.addAction(self.upload_action)
        file_menu.addSeparator()
        file_menu.addAction(self.print_action)
        file_menu.addAction(self.print_preview_action)
        file_menu.addSeparator()
        file_menu.addAction(self.close_tab_action)
        file_menu.addSeparator()
        file_menu.addAction(self.quit_action)

        edit_menu = self.menuBar().addMenu(self.tr("&Edit"))
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.copy_data_uri_action)
        edit_menu.addAction(self.copy_path_action)
        edit_menu.addAction(self.rename_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addAction(self.paste_embedded_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.crop_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.scale_action)
        edit_menu.addAction(self.rotate_action)
        effects_menu = edit_menu.addMenu(self._load_icon("effect"), self.tr("Effects"))
        effects_menu.addAction(self.no_effect_action)
        effects_menu.addAction(self.drop_shadow_effect_action)
        effects_menu.addSeparator()
        effects_menu.addAction(self.grayscale_action)
        effects_menu.addAction(self.invert_color_action)
        effects_menu.addAction(self.border_effect_action)
        edit_menu.addAction(self.add_watermark_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_image_action)
        edit_menu.addAction(self.delete_action)
        annotation_edit_menu = edit_menu.addMenu(self.tr("Annotation Items"))
        annotation_edit_menu.addAction(self.copy_item_action)
        annotation_edit_menu.addAction(self.paste_item_action)
        annotation_edit_menu.addAction(self.duplicate_action)
        annotation_edit_menu.addAction(self.edit_text_action)
        annotation_edit_menu.addSeparator()
        annotation_edit_menu.addAction(self.bring_to_front_action)
        annotation_edit_menu.addAction(self.send_to_back_action)

        view_menu = self.menuBar().addMenu(self.tr("&View"))
        view_menu.addAction(self.open_directory_action)
        view_menu.addAction(self.toggle_docks_action)
        view_menu.addAction(self.modify_canvas_action)
        zoom_menu = view_menu.addMenu(self.tr("Zoom"))
        zoom_menu.addAction(self.zoom_in_action)
        zoom_menu.addAction(self.zoom_out_action)
        zoom_menu.addAction(self.zoom_reset_action)
        zoom_menu.addAction(self.zoom_fit_action)

        options_menu = self.menuBar().addMenu(self.tr("&Options"))
        options_menu.addAction(self.pin_action)
        options_menu.addAction(self.ocr_action)
        options_menu.addAction(self.settings_action)

        watermark_menu = options_menu.addMenu(self.tr("Watermark"))
        watermark_menu.addAction(self.update_watermark_action)
        watermark_menu.addAction(self.rotate_watermark_action)

        annotation_tools_menu = options_menu.addMenu(self.tr("Annotation Tools"))
        for action in (
            self.select_action,
            self.duplicate_tool_action,
            self.pen_action,
            self.marker_pen_action,
            self.marker_rect_action,
            self.marker_ellipse_action,
            self.line_action,
            self.arrow_action,
            self.double_arrow_action,
            self.rect_action,
            self.ellipse_action,
            self.text_action,
            self.text_pointer_action,
            self.text_arrow_action,
            self.number_action,
            self.number_pointer_action,
            self.number_arrow_action,
            self.blur_action,
            self.pixelate_action,
            self.sticker_action,
            self.color_action,
        ):
            annotation_tools_menu.addAction(action)

        help_menu = self.menuBar().addMenu(self.tr("&Help"))
        help_menu.addAction(self.about_action)

    def current_canvas(self) -> AnnotationCanvas | None:
        return self._canvas_from_tab_widget(self.tabs.currentWidget())

    def current_scroll_area(self) -> QScrollArea | None:
        widget = self.tabs.currentWidget()
        return widget if isinstance(widget, QScrollArea) else None

    def _canvas_from_tab_widget(self, widget: QWidget | None) -> AnnotationCanvas | None:
        if isinstance(widget, AnnotationCanvas):
            return widget
        if isinstance(widget, QScrollArea):
            inner = widget.widget()
            return inner if isinstance(inner, AnnotationCanvas) else None
        return None

    def _setup_tray_icon(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return
        tray_icon = QSystemTrayIcon(self)
        icon = self.windowIcon()
        if icon.isNull():
            icon = QIcon.fromTheme("ksnip")
        if icon.isNull():
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        tray_icon.setIcon(icon)
        tray_icon.setToolTip("ksnip PyQt6")
        tray_icon.activated.connect(self._handle_tray_activated)

        menu = QMenu(self)
        menu.addAction(self.tr("Show Editor"), self.show_from_tray)
        menu.addSeparator()
        menu.addAction(self.new_capture_rect_action)
        menu.addAction(self.new_capture_last_rect_action)
        menu.addAction(self.new_capture_full_action)
        menu.addAction(self.new_capture_current_action)
        menu.addAction(self.new_capture_active_action)
        menu.addAction(self.new_capture_under_cursor_action)
        menu.addAction(self.new_capture_portal_action)
        menu.addSeparator()
        menu.addAction(self.open_action)
        menu.addAction(self.save_action)
        menu.addAction(self.paste_action)
        menu.addAction(self.copy_action)
        menu.addAction(self.upload_action)
        menu.addAction(self.ocr_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        tray_icon.setContextMenu(menu)
        self._tray_icon = tray_icon
        self._apply_tray_settings()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self._should_close_to_tray():
            event.ignore()
            self.hide_to_tray(self.tr("ksnip PyQt6 is still running in the system tray."))
            return
        if not self._confirm_close_all_tabs():
            event.ignore()
            return
        self.close_all_pin_windows()
        self._save_ui_settings()
        super().closeEvent(event)

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.WindowStateChange and self._should_minimize_to_tray() and self.isMinimized():
            self.hide_to_tray(self.tr("ksnip PyQt6 was minimized to the system tray."))
        super().changeEvent(event)

    def new_tab(self, image: QImage | None = None, path: str | None = None, title: str = "Untitled") -> AnnotationCanvas:
        canvas = AnnotationCanvas()
        canvas.changed.connect(self._sync_tab_title)
        canvas.changed.connect(self._update_actions)
        canvas.changed.connect(self._sync_item_controls)
        canvas.zoom_changed.connect(self._sync_zoom_controls)
        canvas.set_pen_width(self.stroke_width.value())
        canvas.set_font_family(self.font_family.currentFont().family())
        canvas.set_font_point_size(self.font_size.value())
        canvas.set_text_color(QColor("#ffffff"))
        canvas.set_fill_mode(self._current_fill_mode_value())
        canvas.set_bold(self.bold.isChecked())
        canvas.set_italic(self.italic.isChecked())
        canvas.set_underline(self.underline_button.isChecked())
        canvas.set_shadow(self.shadow_state_button.isChecked())
        canvas.set_scaling(self.scaling.value() / 100.0)
        canvas.set_number_seed(self.number_value.value())
        canvas.set_sticker_paths(self._default_sticker_paths())
        if self._default_sticker_paths():
            canvas.set_sticker_path(self._default_sticker_paths()[0])
        canvas.set_tool(self._current_tool())
        if image is not None:
            canvas.set_image(image, path)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(False)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setBackgroundRole(canvas.backgroundRole())
        scroll_area.setWidget(canvas)
        index = self.tabs.addTab(scroll_area, title)
        self.tabs.setCurrentIndex(index)
        self._update_actions()
        self._sync_item_controls()
        self._sync_zoom_controls(canvas.zoom_percent())
        return canvas

    def set_tool(self, tool: Tool) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            canvas.set_tool(tool)
        if tool == Tool.LINE:
            self._set_tool_group_default_action("arrow", self.line_action)
        elif tool == Tool.ARROW:
            self._set_tool_group_default_action("arrow", self.arrow_action)
        elif tool == Tool.DOUBLE_ARROW:
            self._set_tool_group_default_action("arrow", self.double_arrow_action)
        elif tool == Tool.PEN:
            self.pen_action.setChecked(True)
        elif tool == Tool.MARKER_PEN:
            self._set_tool_group_default_action("marker", self.marker_pen_action)
        elif tool == Tool.MARKER_RECT:
            self._set_tool_group_default_action("marker", self.marker_rect_action)
        elif tool == Tool.MARKER_ELLIPSE:
            self._set_tool_group_default_action("marker", self.marker_ellipse_action)
        elif tool == Tool.TEXT:
            self._set_tool_group_default_action("text", self.text_action)
        elif tool == Tool.TEXT_POINTER:
            self._set_tool_group_default_action("text", self.text_pointer_action)
        elif tool == Tool.TEXT_ARROW:
            self._set_tool_group_default_action("text", self.text_arrow_action)
        elif tool == Tool.NUMBER:
            self._set_tool_group_default_action("number", self.number_action)
        elif tool == Tool.NUMBER_POINTER:
            self._set_tool_group_default_action("number", self.number_pointer_action)
        elif tool == Tool.NUMBER_ARROW:
            self._set_tool_group_default_action("number", self.number_arrow_action)
        elif tool == Tool.BLUR:
            self._set_tool_group_default_action("effect", self.blur_action)
        elif tool == Tool.PIXELATE:
            self._set_tool_group_default_action("effect", self.pixelate_action)
        elif tool == Tool.RECT:
            self._set_tool_group_default_action("shape", self.rect_action)
        elif tool == Tool.ELLIPSE:
            self._set_tool_group_default_action("shape", self.ellipse_action)
        elif tool == Tool.STICKER:
            self.sticker_action.setChecked(True)
        self.select_action.setChecked(tool == Tool.SELECT)
        self.pen_action.setChecked(tool == Tool.PEN)
        self.marker_pen_action.setChecked(tool == Tool.MARKER_PEN)
        self.line_action.setChecked(tool == Tool.LINE)
        self.arrow_action.setChecked(tool == Tool.ARROW)
        self.double_arrow_action.setChecked(tool == Tool.DOUBLE_ARROW)
        self.rect_action.setChecked(tool == Tool.RECT)
        self.ellipse_action.setChecked(tool == Tool.ELLIPSE)
        self.marker_rect_action.setChecked(tool == Tool.MARKER_RECT)
        self.marker_ellipse_action.setChecked(tool == Tool.MARKER_ELLIPSE)
        self.text_action.setChecked(tool == Tool.TEXT)
        self.text_pointer_action.setChecked(tool == Tool.TEXT_POINTER)
        self.text_arrow_action.setChecked(tool == Tool.TEXT_ARROW)
        self.number_action.setChecked(tool == Tool.NUMBER)
        self.number_pointer_action.setChecked(tool == Tool.NUMBER_POINTER)
        self.number_arrow_action.setChecked(tool == Tool.NUMBER_ARROW)
        self.blur_action.setChecked(tool == Tool.BLUR)
        self.pixelate_action.setChecked(tool == Tool.PIXELATE)
        self.sticker_action.setChecked(tool == Tool.STICKER)
        self.crop_action.setChecked(tool == Tool.CROP)
        self._settings.setValue("editor/tool", tool.value)
        self._sync_item_controls()
        self._update_property_toolbar_for_tool()

    def select_color(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        options = QColorDialog.ColorDialogOption(0)
        effective_tool = self._effective_property_tool()
        if effective_tool not in {Tool.MARKER_PEN, Tool.MARKER_RECT, Tool.MARKER_ELLIPSE}:
            options |= QColorDialog.ColorDialogOption.ShowAlphaChannel
        color = QColorDialog.getColor(canvas.color(), self, self.tr("Select color"), options)
        if color.isValid():
            self._apply_selected_color(color)

    def _apply_selected_color(self, color: QColor) -> None:
        canvas = self.current_canvas()
        if canvas is None or not color.isValid():
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_color_to_selected_item(color):
            self.status_label.setText(self.tr("Updated selected item color"))
        else:
            canvas.set_color(color)
        self._sync_toolbox_color_button(color)
        self._sync_property_color_buttons()

    def select_fill_color(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        color = QColorDialog.getColor(parent=self)
        if not color.isValid():
            return
        alpha = self.opacity.value() / 100.0
        color.setAlphaF(alpha)
        if canvas.tool() == Tool.SELECT and canvas.apply_fill_color_to_selected_item(color):
            self.status_label.setText(self.tr("Updated selected item fill"))
            self._sync_property_color_buttons()
            return
        canvas.set_fill_color(color)
        self._sync_property_color_buttons()

    def select_text_color(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        color = QColorDialog.getColor(canvas.text_color(), self, self.tr("Select text color"), QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if not color.isValid():
            return
        self._apply_selected_text_color(color)

    def _apply_selected_text_color(self, color: QColor) -> None:
        canvas = self.current_canvas()
        if canvas is None or not color.isValid():
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_text_color_to_selected_item(color):
            self.status_label.setText(self.tr("Updated selected text color"))
        else:
            canvas.set_text_color(color)
        self._sync_property_color_buttons()

    def _apply_stroke_width(self, width: int) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            if canvas.tool() == Tool.SELECT and canvas.apply_pen_width_to_selected_item(width):
                self.status_label.setText(self.tr("Updated selected item width to %1").replace("%1", str(width)))
                self._sync_auxiliary_property_controls()
                return
            canvas.set_pen_width(width)
        self._sync_auxiliary_property_controls()
        self._settings.setValue("editor/pen_width", width)

    def _apply_font_family(self, font) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        family = font.family()
        if canvas.tool() == Tool.SELECT and canvas.apply_font_family_to_selected_text(family):
            self.status_label.setText(self.tr("Updated selected text font"))
            return
        canvas.set_font_family(family)
        self._settings.setValue("editor/font_family", family)

    def _apply_font_size(self, size: int) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_font_point_size_to_selected_text(size):
            self.status_label.setText(self.tr("Updated selected text size to %1").replace("%1", str(size)))
            return
        canvas.set_font_point_size(size)
        self._settings.setValue("editor/font_point_size", size)

    def _apply_opacity(self, opacity: int) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_opacity_to_selected_item(opacity):
            self.status_label.setText(self.tr("Updated selected item opacity to %1%").replace("%1", str(opacity)))
            return
        canvas.set_opacity(opacity / 100.0)
        self._settings.setValue("editor/opacity_percent", opacity)

    def _apply_capture_delay(self, seconds: int) -> None:
        self._settings.setValue("capture/delay_seconds", max(0, int(seconds)))

    def _apply_fill_mode(self, index: int) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        fill_mode = self.fill_mode.itemData(index)
        if fill_mode is None:
            return
        self._sync_fill_mode_button()
        if canvas.tool() == Tool.SELECT and canvas.apply_fill_mode_to_selected_item(fill_mode):
            self.status_label.setText(self.tr("Updated selected item fill mode"))
            return
        canvas.set_fill_mode(fill_mode)
        self._settings.setValue("editor/fill_mode", fill_mode.value)

    def _apply_bold(self, checked: bool) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_bold_to_selected_text(checked):
            self.status_label.setText(self.tr("Updated selected text bold style"))
            return
        canvas.set_bold(checked)
        self._settings.setValue("editor/bold", checked)

    def _apply_italic(self, checked: bool) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.apply_italic_to_selected_text(checked):
            self.status_label.setText(self.tr("Updated selected text italic style"))
            return
        canvas.set_italic(checked)
        self._settings.setValue("editor/italic", checked)

    def _apply_underline(self, checked: bool) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            if canvas.tool() == Tool.SELECT and canvas.apply_underline_to_selected_text(checked):
                self.status_label.setText(self.tr("Updated selected text underline style"))
                return
            canvas.set_underline(checked)
        self._settings.setValue("editor/underline", checked)

    def _apply_shadow_enabled(self, checked: bool) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            if canvas.tool() == Tool.SELECT and canvas.apply_shadow_to_selected_item(checked):
                self.status_label.setText(self.tr("Updated selected item shadow"))
            else:
                canvas.set_shadow(checked)
        self._sync_auxiliary_property_controls()
        self._settings.setValue("editor/shadow_enabled", checked)

    def _apply_scaling(self, value: int) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            if canvas.tool() == Tool.SELECT and canvas.apply_scaling_to_selected_item(value):
                self.status_label.setText(self.tr("Updated selected item scale to %1%").replace("%1", str(value)))
            else:
                canvas.set_scaling(value / 100.0)
        self._settings.setValue("editor/scaling_percent", value)

    def _apply_number_value(self, value: int) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            if canvas.tool() == Tool.SELECT and canvas.apply_number_to_selected_item(value):
                self.status_label.setText(self.tr("Updated selected number to %1").replace("%1", str(value)))
            else:
                canvas.set_number_seed(value)

    def _apply_blur_strength(self, value: int) -> None:
        if self.stroke_width.value() != value:
            self.stroke_width.blockSignals(True)
            self.stroke_width.setValue(value)
            self.stroke_width.blockSignals(False)
        canvas = self.current_canvas()
        if canvas is not None:
            canvas.set_pen_width(value)
        self._settings.setValue("editor/pen_width", value)

    def _sync_item_controls(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.tool() == Tool.SELECT and canvas.has_selected_item():
            selected_width = canvas.selected_item_pen_width()
            if selected_width is not None and self.stroke_width.value() != selected_width:
                self.stroke_width.blockSignals(True)
                self.stroke_width.setValue(selected_width)
                self.stroke_width.blockSignals(False)

            selected_font_size = canvas.selected_item_font_point_size()
            if selected_font_size is not None and self.font_size.value() != selected_font_size:
                self.font_size.blockSignals(True)
                self.font_size.setValue(selected_font_size)
                self.font_size.blockSignals(False)

            selected_font_family = canvas.selected_item_font_family()
            if selected_font_family is not None and self.font_family.currentFont().family() != selected_font_family:
                self.font_family.blockSignals(True)
                self.font_family.setCurrentFont(QFont(selected_font_family))
                self.font_family.blockSignals(False)

            selected_opacity = canvas.selected_item_opacity()
            if selected_opacity is not None and self.opacity.value() != selected_opacity:
                self.opacity.blockSignals(True)
                self.opacity.setValue(selected_opacity)
                self.opacity.blockSignals(False)

            selected_fill_mode = canvas.selected_item_fill_mode()
            if selected_fill_mode is not None:
                index = self.fill_mode.findData(selected_fill_mode)
                if index >= 0 and self.fill_mode.currentIndex() != index:
                    self.fill_mode.blockSignals(True)
                    self.fill_mode.setCurrentIndex(index)
                    self.fill_mode.blockSignals(False)
                    self._sync_fill_mode_button()

            selected_bold = canvas.selected_item_bold()
            if selected_bold is not None and self.bold.isChecked() != selected_bold:
                self.bold.blockSignals(True)
                self.bold.setChecked(selected_bold)
                self.bold.blockSignals(False)

            selected_italic = canvas.selected_item_italic()
            if selected_italic is not None and self.italic.isChecked() != selected_italic:
                self.italic.blockSignals(True)
                self.italic.setChecked(selected_italic)
                self.italic.blockSignals(False)

            selected_underline = canvas.selected_item_underline()
            if selected_underline is not None and self.underline_button.isChecked() != selected_underline:
                self.underline_button.blockSignals(True)
                self.underline_button.setChecked(selected_underline)
                self.underline_button.blockSignals(False)

            selected_shadow = canvas.selected_item_shadow()
            if selected_shadow is not None and self.shadow_state_button.isChecked() != selected_shadow:
                self.shadow_state_button.blockSignals(True)
                self.shadow_state_button.setChecked(selected_shadow)
                self.shadow_state_button.blockSignals(False)

            selected_scaling = canvas.selected_item_scaling()
            if selected_scaling is not None and self.scaling.value() != selected_scaling:
                self.scaling.blockSignals(True)
                self.scaling.setValue(selected_scaling)
                self.scaling.blockSignals(False)

            selected_number = canvas.selected_item_number()
            if selected_number is not None and self.number_value.value() != selected_number:
                self.number_value.blockSignals(True)
                self.number_value.setValue(selected_number)
                self.number_value.blockSignals(False)

            selected_color = canvas.selected_item_color()
            if selected_color is not None:
                self._sync_toolbox_color_button(selected_color)
                self._sync_property_color_buttons()
                self._sync_fill_mode_button()
                self._sync_auxiliary_property_controls()
                return
        else:
            if self.number_value.value() != canvas.number_seed():
                self.number_value.blockSignals(True)
                self.number_value.setValue(canvas.number_seed())
                self.number_value.blockSignals(False)
        self._sync_toolbox_color_button()
        self._sync_property_color_buttons()
        self._sync_fill_mode_button()
        self._sync_auxiliary_property_controls()
        self._update_property_toolbar_for_tool()

    def set_current_canvas_zoom(self, percent: int) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        canvas.set_zoom_percent(percent)

    def zoom_in_current_canvas(self) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            canvas.zoom_in()

    def zoom_out_current_canvas(self) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            canvas.zoom_out()

    def reset_zoom_current_canvas(self) -> None:
        canvas = self.current_canvas()
        if canvas is not None:
            canvas.reset_zoom()

    def fit_current_canvas(self) -> None:
        canvas = self.current_canvas()
        scroll_area = self.current_scroll_area()
        if canvas is None or scroll_area is None:
            return
        canvas.fit_to_size(scroll_area.viewport().size())

    def _sync_zoom_controls(self, percent: int) -> None:
        if self.zoom_spinbox.value() == percent:
            return
        self.zoom_spinbox.blockSignals(True)
        self.zoom_spinbox.setValue(percent)
        self.zoom_spinbox.blockSignals(False)

    def capture_fullscreen(self) -> None:
        self._settings.setValue("capture/default_mode", "full")
        result = self._capture_with_preferences(grab_fullscreen, portal_interactive=False)
        if result is None:
            self._handle_capture_failure("Unable to capture full screen.")
            return
        self._load_capture_result(result, "Full Screen")

    def capture_current_screen(self) -> None:
        self._settings.setValue("capture/default_mode", "current")
        result = self._capture_with_preferences(grab_current_screen)
        if result is None:
            self._handle_capture_failure("Unable to capture current screen.")
            return
        self._load_capture_result(result, "Current Screen")

    def capture_rect_area(self) -> None:
        self._settings.setValue("capture/default_mode", "rect")
        result = self._capture_with_preferences(lambda: grab_rectangular_area())
        if result is None:
            self._handle_capture_failure("Capture canceled", critical=False)
            return
        self._load_capture_result(result, "Rect Area")

    def capture_last_rect_area(self) -> None:
        self._settings.setValue("capture/default_mode", "last_rect")
        result = self._capture_with_preferences(grab_last_rectangular_area)
        if result is None:
            if has_last_rectangular_area():
                self._handle_capture_failure("Unable to capture the last rectangular area.")
            else:
                self._handle_capture_failure("No previous rectangular area capture is available yet.")
            return
        self._load_capture_result(result, "Last Rect Area")

    def capture_active_window(self) -> None:
        self._settings.setValue("capture/default_mode", "active")
        result = self._capture_with_preferences(grab_active_window)
        if result is None:
            self._handle_capture_failure("Unable to capture active window.")
            return
        self._load_capture_result(result, "Active Window")

    def capture_window_under_cursor(self) -> None:
        self._settings.setValue("capture/default_mode", "under_cursor")
        result = self._capture_with_preferences(grab_window_under_cursor)
        if result is None:
            self._handle_capture_failure("Unable to capture window under cursor.")
            return
        self._load_capture_result(result, "Window Under Cursor")

    def capture_portal(self) -> None:
        self._settings.setValue("capture/default_mode", "portal")
        result = self._capture_with_preferences(
            lambda: grab_portal(
                interactive=True,
                scale=self._setting_bool("capture/scale_generic_wayland", False),
            ),
            allow_forced_portal=False,
        )
        if result is None:
            message = portal_failure_message()
            if portal_capture_was_canceled():
                self._handle_capture_failure(self.tr("Portal capture canceled."), critical=False)
            else:
                self._handle_capture_failure(message)
            return
        self._load_capture_result(result, "Portal")

    def _capture_with_preferences(self, capture_fn, *, portal_interactive: bool = True, allow_forced_portal: bool = True):
        use_portal = allow_forced_portal and (
            self._setting_bool("capture/force_generic_wayland", False) or is_wayland_session()
        )
        self._last_capture_used_portal = use_portal or not allow_forced_portal
        if use_portal:
            capture_fn = lambda: grab_portal(
                interactive=portal_interactive,
                scale=self._setting_bool("capture/scale_generic_wayland", False),
            )
        was_visible = self.isVisible() and not self.isMinimized()
        should_hide = self._setting_bool("capture/hide_main_window", True) and was_visible
        if should_hide:
            self.hide()
            QGuiApplication.processEvents()

        delay_seconds = (
            self._capture_delay_override_seconds
            if self._capture_delay_override_seconds is not None
            else self._setting_int("capture/delay_seconds", 0)
        )
        self._capture_delay_override_seconds = None
        include_cursor = (
            self._capture_cursor_override
            if self._capture_cursor_override is not None
            else self._setting_bool("capture/include_cursor", True)
        )
        self._capture_cursor_override = None
        delay_ms = max(0, delay_seconds * 1000)
        if was_visible:
            delay_ms = max(delay_ms, max(0, self._setting_int("capture/implicit_delay_ms", 200)))
        if delay_ms > 0:
            self._wait_for_capture_delay(delay_ms)

        try:
            result = capture_fn()
            if result is not None and include_cursor:
                cursor = grab_x11_cursor()
                if cursor is not None:
                    cursor_image, cursor_global_position = cursor
                    cursor_position = cursor_global_position - result.global_origin
                    cursor_rect = QRectF(cursor_position.x(), cursor_position.y(), cursor_image.width(), cursor_image.height())
                    capture_rect = QRectF(0, 0, result.pixmap.width(), result.pixmap.height())
                    if cursor_rect.intersects(capture_rect):
                        result.cursor_image = cursor_image
                        result.cursor_position = cursor_position
        finally:
            if should_hide and self._setting_bool("capture/show_main_window_after_capture", True):
                self.showNormal()
                self.raise_()
                self.activateWindow()

        return result

    def _wait_for_capture_delay(self, delay_ms: int) -> None:
        loop = QEventLoop(self)
        QTimer.singleShot(delay_ms, loop.quit)
        loop.exec()

    def _load_capture_result(self, result, title: str) -> None:
        if self._cli_direct_save or self._cli_upload:
            self._process_cli_capture(result)
            return
        self._load_capture(result.pixmap.toImage(), title)
        canvas = self.current_canvas()
        if canvas is not None and result.cursor_image is not None and result.cursor_position is not None:
            canvas.add_image_item(result.cursor_image, position=result.cursor_position)
        if self._setting_bool("saver/auto_save", False):
            self._auto_save_current_capture()
        if self._setting_bool("capture/auto_copy_new_captures", False):
            QGuiApplication.clipboard().setImage(result.pixmap.toImage())
            self.status_label.setText(
                self.tr("Loaded %1 capture and copied it to clipboard").replace("%1", title.lower())
            )

    def _process_cli_capture(self, result) -> None:
        image = self._cli_capture_image(result)
        if self._cli_direct_save:
            self._save_cli_capture(image)
        if self._cli_upload:
            self._upload_cli_capture(image)
        self._finish_cli_capture()

    @staticmethod
    def _cli_capture_image(result) -> QImage:
        image = result.pixmap.toImage()
        if result.cursor_image is not None and result.cursor_position is not None:
            image = image.copy()
            painter = QPainter(image)
            painter.drawImage(result.cursor_position, result.cursor_image)
            painter.end()
        return image

    def _save_cli_capture(self, image: QImage) -> bool:
        path = Path(self._cli_save_path).expanduser() if self._cli_save_path else self._next_auto_save_path()
        if not path.suffix:
            path = path.with_suffix(".png")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            print(f"Unable to create capture directory {path.parent}: {error}", file=sys.stderr)
            return False
        quality = self._setting_int("saver/quality_factor", 50) if self._setting_bool("saver/quality_enabled", False) else -1
        if not image.save(str(path), None, quality):
            print(f"Unable to save screenshot to {path}", file=sys.stderr)
            return False
        print(path)
        return True

    def _upload_cli_capture(self, image: QImage) -> bool:
        result = self._script_uploader.upload(
            image,
            script_path=str(self._settings.value("upload/script_path", "")),
            copy_output_filter=str(self._settings.value("upload/output_filter", "")),
            stop_on_stderr=self._setting_bool("upload/stop_on_stderr", False),
        )
        if not result.ok:
            print(f"Upload failed: {result.message}", file=sys.stderr)
            if result.output:
                print(result.output, file=sys.stderr)
            return False
        print("Upload finished")
        if result.output:
            print(result.output)
            if self._setting_bool("upload/copy_output", False):
                QGuiApplication.clipboard().setText(result.output)
        return True

    def _finish_cli_capture(self) -> None:
        should_quit = self._quit_after_capture
        self._cli_direct_save = False
        self._cli_save_path = None
        self._cli_upload = False
        self._quit_after_capture = False
        if should_quit:
            QTimer.singleShot(0, QApplication.quit)

    def _handle_capture_failure(self, message: str, *, critical: bool = True) -> None:
        if self._last_capture_used_portal:
            self._last_capture_used_portal = False
            if portal_capture_was_canceled():
                message = self.tr("Portal capture canceled.")
                critical = False
            else:
                message = portal_failure_message()
                critical = True
        if self._quit_after_capture:
            print(message, file=sys.stderr)
            self._finish_cli_capture()
        elif critical:
            self._show_error(message)
        else:
            self.status_label.setText(message)

    def _load_capture(self, image: QImage, title: str) -> None:
        canvas = self.current_canvas()
        if canvas is None or canvas.has_image():
            canvas = self.new_tab()
        canvas.set_image(image, dirty=True)
        self.tabs.setTabText(self.tabs.currentIndex(), title)
        self._sync_tab_title()
        self.status_label.setText(self.tr("Loaded %1 capture").replace("%1", title.lower()))
        self._update_actions()
        self._schedule_resize_to_content()

    def _auto_save_current_capture(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        path = self._next_auto_save_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self._show_error(f"Unable to create capture directory {path.parent}: {error}")
            return
        self._save_canvas_to_path(canvas, self.tabs.currentIndex(), str(path))

    def _next_auto_save_path(self, now: datetime | None = None) -> Path:
        now = now or datetime.now()
        template = str(
            self._settings.value(
                "saver/location",
                str(Path.home() / "Pictures" / "$Y$M$D-$T.png"),
            )
        ).strip()
        if not template:
            template = str(Path.home() / "Pictures" / "$Y$M$D-$T.png")
        replacements = {
            "$Y": now.strftime("%Y"),
            "$M": now.strftime("%m"),
            "$D": now.strftime("%d"),
            "$h": now.strftime("%H"),
            "$m": now.strftime("%M"),
            "$s": now.strftime("%S"),
            "$T": now.strftime("%H%M%S"),
        }
        for token, value in replacements.items():
            template = template.replace(token, value)

        counter = max(1, self._setting_int("saver/counter", 1))
        counter_pattern = re.compile(r"#+")

        def with_counter(value: int) -> str:
            return counter_pattern.sub(lambda match: str(value).zfill(len(match.group(0))), template)

        candidate = Path(with_counter(counter)).expanduser()
        if not candidate.suffix:
            candidate = candidate.with_suffix(".png")
        overwrite = self._setting_bool("saver/overwrite", False)
        if counter_pattern.search(template):
            while candidate.exists() and not overwrite:
                counter += 1
                candidate = Path(with_counter(counter)).expanduser()
                if not candidate.suffix:
                    candidate = candidate.with_suffix(".png")
            self._settings.setValue("saver/counter", counter + 1)
        elif candidate.exists() and not overwrite:
            stem, suffix = candidate.stem, candidate.suffix
            index = 1
            while candidate.exists():
                candidate = candidate.with_name(f"{stem}-{index}{suffix}")
                index += 1
        return candidate

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open image",
            self._default_image_directory(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not path:
            return
        self._open_image_path(path)

    def save_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        if canvas.state.path:
            self._save_canvas_to_path(canvas, self.tabs.currentIndex(), canvas.state.path)
            return
        self.save_image_as()

    def save_image_as(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save image as",
            canvas.state.path or self._default_image_directory(),
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WebP (*.webp)",
        )
        if not path:
            return
        self._save_canvas_to_path(canvas, self.tabs.currentIndex(), path)

    def save_all_images(self) -> None:
        saved_count = 0
        for index in range(self.tabs.count()):
            canvas = self._canvas_from_tab_widget(self.tabs.widget(index))
            if canvas is None or not canvas.has_image():
                continue
            if canvas.state.path and not canvas.state.dirty:
                continue

            path = canvas.state.path
            if not path:
                self.tabs.setCurrentIndex(index)
                suggested_name = self.tabs.tabText(index).replace(" *", "").strip()
                if not Path(suggested_name).suffix:
                    suggested_name = f"{suggested_name or 'Untitled'}.png"
                path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save image as",
                    str(Path(self._default_image_directory()) / suggested_name),
                    "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WebP (*.webp)",
                )
                if not path:
                    self.status_label.setText(
                        f"Save All canceled after saving {saved_count} image(s)"
                    )
                    return

            if not self._save_canvas_to_path(canvas, index, path, show_status=False):
                return
            saved_count += 1

        self.status_label.setText(self.tr("Saved %1 image(s)").replace("%1", str(saved_count)))

    def _save_canvas_to_path(
        self,
        canvas: AnnotationCanvas,
        tab_index: int,
        path: str,
        *,
        show_status: bool = True,
    ) -> bool:
        quality = self._setting_int("saver/quality_factor", 50) if self._setting_bool("saver/quality_enabled", False) else -1
        if not canvas.image().save(path, None, quality):
            self._show_error(f"Unable to save image to {path}")
            return False
        canvas.mark_saved(path)
        self._store_recent_image_path(path)
        self.tabs.setTabText(tab_index, Path(path).name)
        if show_status:
            self.status_label.setText(self.tr("Saved %1").replace("%1", str(path)))
        return True

    def copy_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        QGuiApplication.clipboard().setImage(canvas.image())
        self.status_label.setText(self.tr("Copied image to clipboard"))

    def print_current_image(self) -> None:
        if self.current_canvas() is None or not self.current_canvas().has_image():
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            if self._paint_current_image_to_printer(printer):
                self.status_label.setText(self.tr("Sent image to printer"))
            else:
                self._show_error("Unable to render the image for printing.")

    def preview_current_image(self) -> None:
        if self.current_canvas() is None or not self.current_canvas().has_image():
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle(self.tr("Print Preview"))
        preview.paintRequested.connect(self._paint_current_image_to_printer)
        preview.exec()

    def _paint_current_image_to_printer(self, printer: QPrinter) -> bool:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return False
        image = canvas.image()
        page_rect = printer.pageLayout().paintRectPixels(printer.resolution())
        scaled_size = image.size()
        scaled_size.scale(page_rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF(
            page_rect.x() + (page_rect.width() - scaled_size.width()) / 2,
            page_rect.y() + (page_rect.height() - scaled_size.height()) / 2,
            scaled_size.width(),
            scaled_size.height(),
        )
        painter = QPainter()
        if not painter.begin(printer):
            return False
        painter.drawImage(target, image)
        painter.end()
        return True

    def rename_current_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        current_name = Path(canvas.state.path).name if canvas.state.path else self.tabs.tabText(self.tabs.currentIndex()).replace(" *", "")
        name, accepted = QInputDialog.getText(self, "Rename", "New name:", text=current_name)
        if accepted:
            self._rename_current_image_to(name)

    def _rename_current_image_to(self, name: str) -> bool:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return False
        resolved_name = name.strip()
        if not resolved_name or resolved_name in {".", ".."} or Path(resolved_name).name != resolved_name:
            self._show_error("Enter a valid file name without directory separators.")
            return False

        old_path = Path(canvas.state.path) if canvas.state.path else None
        if old_path is not None:
            if not Path(resolved_name).suffix and old_path.suffix:
                resolved_name += old_path.suffix
            new_path = old_path.with_name(resolved_name)
            if new_path == old_path:
                return True
            if new_path.exists():
                self._show_error(f"A file named {new_path.name} already exists.")
                return False
            try:
                old_path.rename(new_path)
            except OSError as error:
                self._show_error(f"Unable to rename {old_path.name}: {error}")
                return False
            canvas.state.path = str(new_path)
            self._remove_recent_image_path(str(old_path))
            self._store_recent_image_path(str(new_path))

        suffix = " *" if canvas.state.dirty else ""
        self.tabs.setTabText(self.tabs.currentIndex(), f"{resolved_name}{suffix}")
        self.status_label.setText(self.tr("Renamed to %1").replace("%1", resolved_name))
        self._update_window_title()
        self._update_actions()
        return True

    def delete_current_image_file(self) -> None:
        self._delete_current_image_file(confirm=True)

    def _delete_current_image_file(self, *, confirm: bool) -> bool:
        canvas = self.current_canvas()
        if canvas is None or not canvas.state.path:
            return False
        path = Path(canvas.state.path)
        if confirm:
            reply = QMessageBox.question(
                self,
                "Delete Image",
                f"The item '{path}' will be deleted.\nDo you want to continue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if reply != QMessageBox.StandardButton.Ok:
                return False
        try:
            path.unlink()
        except OSError as error:
            self._show_error(f"Unable to delete {path}: {error}")
            return False

        index = self.tabs.currentIndex()
        self._remove_recent_image_path(str(path))
        self.tabs.removeTab(index)
        self.status_label.setText(self.tr("Deleted %1").replace("%1", path.name))
        if self.tabs.count() > 0:
            self._handle_current_tab_changed(self.tabs.currentIndex())
        self._update_actions()
        self._update_property_toolbar_for_tool()
        return True

    def copy_image_as_data_uri(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        buffer = QBuffer(self)
        if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            self._show_error("Unable to encode image as a Data URI")
            return
        try:
            if not canvas.image().save(buffer, "PNG"):
                self._show_error("Unable to encode image as a Data URI")
                return
            encoded = bytes(buffer.data().toBase64()).decode("ascii")
        finally:
            buffer.close()
        QGuiApplication.clipboard().setText(f"data:image/png;base64,{encoded}")
        self.status_label.setText(self.tr("Copied image as a base64 encoded Data URI"))

    def copy_image_path(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.state.path:
            return
        QGuiApplication.clipboard().setText(canvas.state.path)
        self.status_label.setText(self.tr("Copied path %1").replace("%1", str(canvas.state.path)))

    def open_image_directory(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.state.path:
            return
        directory = str(Path(canvas.state.path).expanduser().parent)
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(directory)):
            self._show_error(f"Unable to open directory {directory}")
            return
        self.status_label.setText(self.tr("Opened directory %1").replace("%1", str(directory)))

    def copy_selected_item(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.copy_selected_item_to_clipboard():
            self.status_label.setText(self.tr("Copied selected item(s)"))

    def paste_image(self) -> None:
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._show_error("Clipboard does not contain an image.")
            return
        canvas = self.current_canvas()
        if canvas is None or canvas.has_image():
            canvas = self.new_tab()
        canvas.set_image(image, dirty=True)
        self.tabs.setTabText(self.tabs.currentIndex(), "Clipboard")
        self._sync_tab_title()
        self.status_label.setText(self.tr("Loaded image from clipboard"))
        self._update_actions()
        self._schedule_resize_to_content()

    def paste_embedded_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        image = QGuiApplication.clipboard().image()
        if image.isNull():
            self._show_error("Clipboard does not contain an image.")
            return
        base_size = canvas.image().size()
        position = QPoint(
            max(0, (base_size.width() - image.width()) // 2),
            max(0, (base_size.height() - image.height()) // 2),
        )
        if canvas.add_image_item(image, position=position):
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Pasted embedded image from clipboard"))

    def modify_canvas(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        dialog = ModifyCanvasDialog(canvas.background_image(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        rect = dialog.canvas_rect()
        if canvas.modify_canvas_rect(rect, dialog.canvas_color()):
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(
                self.tr("Canvas modified: %1 × %2 px at (%3, %4)")
                .replace("%1", str(rect.width()))
                .replace("%2", str(rect.height()))
                .replace("%3", str(rect.x()))
                .replace("%4", str(rect.y()))
            )

    def toggle_docks(self) -> None:
        self._set_docks_collapsed(self.main_toolbar.isVisible())

    def _set_docks_collapsed(self, collapsed: bool) -> None:
        self._docks_collapsed = collapsed
        self.main_toolbar.setVisible(not collapsed)
        self.properties_toolbar.setVisible(not collapsed and self._property_toolbar_has_controls)
        self.left_toolbar.setVisible(not collapsed)
        self.toggle_docks_action.setText(self.tr("Show Docks") if collapsed else self.tr("Hide Docks"))

    def paste_item(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        if canvas.paste_item_from_clipboard():
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Pasted item from clipboard"))
            return
        self._show_error("Clipboard does not contain a ksnip PyQt6 item.")

    def undo(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        canvas.undo()
        self._sync_tab_title()
        self._update_actions()

    def redo(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        canvas.redo()
        self._sync_tab_title()
        self._update_actions()

    def delete_selected_item(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.delete_selected_item():
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Deleted selected item"))

    def duplicate_selected_item(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.duplicate_selected_item():
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Duplicated selected item"))

    def edit_selected_text(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.edit_selected_text(self):
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Updated text item"))

    def bring_selected_item_to_front(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.bring_selected_item_to_front():
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Brought selected item to front"))

    def send_selected_item_to_back(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.send_selected_item_to_back():
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Sent selected item to back"))

    def rotate_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        dialog = RotateDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        operation, value = dialog.operation()
        if operation == "rotate":
            changed = canvas.rotate(int(value))
            message = self.tr("Rotated image by %1 degrees").replace("%1", str(value))
        else:
            changed = canvas.flip_image(str(value))
            direction = self.tr("Horizontal") if value == "horizontal" else self.tr("Vertical")
            message = self.tr("Flipped image: %1").replace("%1", direction)
        if not changed:
            return
        self._sync_tab_title()
        self._update_actions()
        self.status_label.setText(message)

    def scale_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        dialog = ScaleDialog(canvas.background_image().size(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_size = dialog.new_size()
        if not canvas.scale_to_size(new_size.width(), new_size.height()):
            return
        self._sync_tab_title()
        self._update_actions()
        self.status_label.setText(
            self.tr("Scaled image to %1 × %2 px")
            .replace("%1", str(new_size.width()))
            .replace("%2", str(new_size.height()))
        )

    def apply_image_effect(self, effect: str) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            return
        if canvas.set_image_effect(effect):
            labels = {
                "none": self.tr("No Effect"),
                "drop_shadow": self.tr("Drop Shadow"),
                "grayscale": self.tr("Grayscale"),
                "invert": self.tr("Invert Color"),
                "border": self.tr("Border"),
            }
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Image effect: %1").replace("%1", labels[effect]))

    def _sync_bottom_effect_button(self, action: QAction | None = None) -> None:
        if not hasattr(self, "bottom_effect_button"):
            return
        selected = action or self.image_effect_action_group.checkedAction() or self.no_effect_action
        self.bottom_effect_button.setIcon(selected.icon())
        self.bottom_effect_button.setToolTip(self.tr("Image Effect: %1").replace("%1", selected.text()))

    def cut_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        dialog = CutDialog(canvas.background_image(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if canvas.cut_slice(dialog.cut_rect()):
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Image slice removed"))

    def pin_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        title = self.tabs.tabText(self.tabs.currentIndex()).replace(" *", "") or "Pinned Image"
        pin_window = PinWindow(QPixmap.fromImage(canvas.image()), title)
        pin_window.close_other_requested.connect(self.close_other_pin_windows)
        pin_window.close_all_requested.connect(self.close_all_pin_windows)
        pin_window.destroyed.connect(lambda _=None, window=pin_window: self._forget_pin_window(window))
        self._pin_windows.append(pin_window)
        pin_window.show()
        pin_window.raise_()
        pin_window.activateWindow()
        self.status_label.setText(self.tr("Pinned current image"))

    def open_settings_dialog(self) -> None:
        previous_language = str(self._settings.value("application/language", ""))
        dialog = SettingsDialog(self._current_settings_data(), self._watermark_store, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        settings_data = dialog.settings_data()
        self._apply_settings_data(settings_data)
        if previous_language != settings_data.application_language:
            self.status_label.setText(self.tr("Language changed. Restart ksnip to apply it."))
        else:
            self.status_label.setText(self.tr("Settings updated"))

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self, message: str | None = None) -> None:
        self.hide()
        if self._tray_icon is not None and message and self._setting_bool("tray/notifications", True):
            self._tray_icon.showMessage("ksnip PyQt6", message, QSystemTrayIcon.MessageIcon.Information)

    def quit_application(self) -> None:
        self._allow_quit = True
        if self._tray_icon is not None:
            self._tray_icon.hide()
        self.close_all_pin_windows()
        self.close()
        app = QGuiApplication.instance()
        if app is not None:
            app.quit()

    def add_watermark(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        watermark = self._watermark_store.load()
        if watermark.isNull():
            self._show_error("Watermark image required. Use 'Update Watermark Image…' first.")
            return
        prepared = self._watermark_preparer.prepare(
            watermark,
            canvas.image().size(),
            self.rotate_watermark_action.isChecked(),
        )
        x, y = random_watermark_position(prepared, canvas.image().size())
        if canvas.add_image_item(prepared.toImage(), position=QPoint(x, y)):
            self._sync_tab_title()
            self._update_actions()
            self.status_label.setText(self.tr("Added watermark"))

    def update_watermark_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select watermark image",
            self._default_image_directory(),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not path:
            return
        if not self._watermark_store.save_from_path(path):
            self._show_error(f"Unable to load watermark image: {path}")
            return
        self._settings.setValue("paths/last_image_dir", str(Path(path).parent))
        self.status_label.setText(self.tr("Updated watermark image"))

    def upload_image(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        if self._setting_bool("upload/confirm", False):
            reply = QMessageBox.question(
                self,
                "Upload Image",
                "Upload the current image?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        script_path = self._settings.value("upload/script_path", "")
        if not isinstance(script_path, str) or not script_path:
            self._show_error("No upload script configured. Open Settings and set an upload script first.")
            return
        result = self._script_uploader.upload(
            canvas.image(),
            script_path=script_path,
            copy_output_filter=str(self._settings.value("upload/output_filter", "")),
            stop_on_stderr=self._setting_bool("upload/stop_on_stderr", False),
        )
        if result.ok:
            if self._setting_bool("upload/copy_output", False) and result.output:
                QGuiApplication.clipboard().setText(result.output)
            self.status_label.setText(self.tr("Upload finished successfully"))
            if result.output:
                QMessageBox.information(self, "Upload Successful", result.output)
            return
        self._show_error(result.message)

    def run_ocr(self) -> None:
        canvas = self.current_canvas()
        if canvas is None or not canvas.has_image():
            return
        if not self._setting_bool("ocr/enabled", True):
            self._show_error("OCR is disabled. Enable it in Settings first.")
            return
        if self._ocr_thread is not None:
            return

        options = OcrOptions(
            backend=str(self._settings.value("ocr/backend", "paddleocr")),
            language=str(self._settings.value("ocr/language", "english")),
            script_path=str(self._settings.value("ocr/script_path", "")),
        )
        self._ocr_thread = QThread(self)
        self._ocr_worker = OcrWorker(canvas.image(), self._ocr_backend, options)
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_thread.started.connect(self._ocr_worker.run)
        self._ocr_worker.finished.connect(self._handle_ocr_finished)
        self._ocr_worker.failed.connect(self._handle_ocr_failed)
        self._ocr_worker.cancelled.connect(self._handle_ocr_cancelled)
        self._ocr_worker.finished.connect(self._cleanup_ocr_thread)
        self._ocr_worker.failed.connect(self._cleanup_ocr_thread)
        self._ocr_worker.cancelled.connect(self._cleanup_ocr_thread)
        self._ocr_progress = QProgressDialog("Running OCR text recognition...", "Cancel", 0, 0, self)
        self._ocr_progress.setWindowTitle(self.tr("OCR"))
        self._ocr_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._ocr_progress.canceled.connect(self._cancel_ocr)
        self._ocr_progress.show()
        self.status_label.setText(self.tr("Running OCR..."))
        self._ocr_thread.start()

    def _cancel_ocr(self) -> None:
        if self._ocr_worker is not None:
            self._ocr_worker.cancel()

    def _handle_ocr_finished(self, text: str) -> None:
        if self._setting_bool("ocr/copy_to_clipboard", False) and text:
            QGuiApplication.clipboard().setText(text)
        dialog = OcrResultDialog(text, self)
        dialog.exec()
        self.status_label.setText(self.tr("OCR finished"))

    def _handle_ocr_failed(self, message: str) -> None:
        self.status_label.setText(self.tr("OCR failed"))
        self._show_error(message)

    def _handle_ocr_cancelled(self) -> None:
        self.status_label.setText(self.tr("OCR canceled"))

    def _cleanup_ocr_thread(self, *_args) -> None:
        if self._ocr_progress is not None:
            self._ocr_progress.close()
            self._ocr_progress.deleteLater()
            self._ocr_progress = None
        if self._ocr_thread is not None:
            self._ocr_thread.quit()
            self._ocr_thread.wait()
            self._ocr_thread.deleteLater()
            self._ocr_thread = None
        if self._ocr_worker is not None:
            self._ocr_worker.deleteLater()
            self._ocr_worker = None

    def _set_rotate_watermark(self, checked: bool) -> None:
        self._settings.setValue("watermark/rotate", checked)

    def close_tab(self, index: int) -> None:
        if index < 0:
            return
        canvas = self._canvas_from_tab_widget(self.tabs.widget(index))
        if canvas is not None and not self._confirm_discard_canvas(canvas):
            return
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.status_label.setText(self.tr("Ready"))
        self._update_actions()
        self._update_property_toolbar_for_tool()

    def _sync_tab_title(self) -> None:
        canvas = self.current_canvas()
        if canvas is None:
            self._update_window_title()
            return
        index = self.tabs.currentIndex()
        name = Path(canvas.state.path).name if canvas.state.path else self.tabs.tabText(index).replace(" *", "") or "Untitled"
        suffix = " *" if canvas.state.dirty else ""
        self.tabs.setTabText(index, f"{name}{suffix}")
        self._update_window_title()

    def _update_window_title(self) -> None:
        canvas = self.current_canvas()
        title = "ksnip"
        if canvas is not None and canvas.state.path:
            title += f" [{canvas.state.path}]"
        if canvas is not None and canvas.state.dirty:
            title = f"*{title} - Unsaved"
        self.setWindowTitle(title)

    def _update_actions(self) -> None:
        canvas = self.current_canvas()
        has_image = canvas is not None and canvas.has_image()
        has_selected_item = canvas is not None and canvas.has_selected_item()
        can_edit_text = canvas is not None and canvas.selected_item_kind() in (Tool.TEXT, Tool.TEXT_POINTER, Tool.TEXT_ARROW)
        self.save_action.setEnabled(has_image)
        self.save_as_action.setEnabled(has_image)
        self.save_all_action.setEnabled(
            any(
                (tab_canvas := self._canvas_from_tab_widget(self.tabs.widget(index))) is not None
                and tab_canvas.has_image()
                for index in range(self.tabs.count())
            )
        )
        self.print_action.setEnabled(has_image)
        self.print_preview_action.setEnabled(has_image)
        self.copy_action.setEnabled(has_image)
        self.copy_data_uri_action.setEnabled(has_image)
        has_path = canvas is not None and bool(canvas.state.path)
        self.copy_path_action.setEnabled(has_path)
        self.rename_action.setEnabled(has_image)
        self.delete_image_action.setEnabled(has_path)
        self.open_directory_action.setEnabled(has_path)
        self.copy_item_action.setEnabled(has_selected_item)
        self.paste_action.setEnabled(True)
        clipboard_mime_data = QGuiApplication.clipboard().mimeData()
        self.paste_embedded_action.setEnabled(
            has_image and clipboard_mime_data is not None and clipboard_mime_data.hasImage()
        )
        self.paste_item_action.setEnabled(has_image)
        self.undo_action.setEnabled(canvas is not None and canvas.can_undo())
        self.redo_action.setEnabled(canvas is not None and canvas.can_redo())
        self.pin_action.setEnabled(has_image)
        self.add_watermark_action.setEnabled(has_image)
        self.upload_action.setEnabled(has_image)
        self.ocr_action.setEnabled(has_image and self._setting_bool("ocr/enabled", True))
        self.new_capture_last_rect_action.setEnabled(has_last_rectangular_area())
        self.delete_action.setEnabled(has_selected_item)
        self.duplicate_action.setEnabled(has_selected_item)
        self.edit_text_action.setEnabled(can_edit_text)
        self.bring_to_front_action.setEnabled(canvas is not None and canvas.can_bring_selected_item_to_front())
        self.send_to_back_action.setEnabled(canvas is not None and canvas.can_send_selected_item_to_back())
        self.rotate_action.setEnabled(has_image)
        self.scale_action.setEnabled(has_image)
        self.crop_action.setEnabled(has_image)
        self.cut_action.setEnabled(has_image)
        self.grayscale_action.setEnabled(has_image)
        self.invert_color_action.setEnabled(has_image)
        self.border_effect_action.setEnabled(has_image)
        self.no_effect_action.setEnabled(has_image)
        self.drop_shadow_effect_action.setEnabled(has_image)
        if canvas is not None:
            effect_actions = {
                "none": self.no_effect_action,
                "drop_shadow": self.drop_shadow_effect_action,
                "grayscale": self.grayscale_action,
                "invert": self.invert_color_action,
                "border": self.border_effect_action,
            }
            effect_actions[canvas.image_effect()].setChecked(True)
        self._sync_bottom_effect_button()
        self.modify_canvas_action.setEnabled(has_image)
        self.bottom_effect_button.setEnabled(has_image)
        self.close_tab_action.setEnabled(canvas is not None)
        self.recent_images_menu.setEnabled(bool(self._recent_image_paths))
        self.zoom_spinbox.setEnabled(has_image)
        self.zoom_in_action.setEnabled(has_image)
        self.zoom_out_action.setEnabled(has_image)
        self.zoom_reset_action.setEnabled(has_image)
        self.zoom_in_button.setEnabled(has_image)
        self.zoom_out_button.setEnabled(has_image)
        self.zoom_reset_button.setEnabled(has_image)
        self.zoom_fit_button.setEnabled(has_image)

    def _handle_current_tab_changed(self, index: int) -> None:
        del index
        self._update_window_title()
        self._update_actions()
        self._sync_item_controls()
        canvas = self.current_canvas()
        if canvas is not None:
            self._sync_zoom_controls(canvas.zoom_percent())

    def _open_image_path(self, path: str) -> bool:
        image = QImage(path)
        if image.isNull():
            self._remove_recent_image_path(path)
            self._show_error(f"Unable to open image: {path}")
            return False
        title = Path(path).name
        canvas = self.current_canvas()
        if canvas is None or canvas.has_image():
            canvas = self.new_tab()
        canvas.set_image(image, path)
        self._store_recent_image_path(path)
        self.tabs.setTabText(self.tabs.currentIndex(), title)
        self._update_window_title()
        self.status_label.setText(self.tr("Opened %1").replace("%1", title))
        self._update_actions()
        self._schedule_resize_to_content()
        return True

    def _open_image_data(self, data: bytes, title: str = "stdin") -> bool:
        image = QImage.fromData(data)
        if image.isNull():
            self._show_error(self.tr("Unable to open image data."))
            return False
        canvas = self.current_canvas()
        if canvas is None or canvas.has_image():
            canvas = self.new_tab()
        canvas.set_image(image, dirty=True)
        self.tabs.setTabText(self.tabs.currentIndex(), title)
        self._update_window_title()
        self.status_label.setText(self.tr("Opened image from standard input"))
        self._update_actions()
        self._schedule_resize_to_content()
        return True

    def _schedule_resize_to_content(self) -> None:
        if not self._setting_bool("application/auto_resize_to_content", True):
            return
        delay = max(0, self._setting_int("application/resize_delay_ms", 10))
        QTimer.singleShot(delay, self._resize_window_to_content)

    def _resize_window_to_content(self) -> None:
        canvas = self.current_canvas()
        screen = QGuiApplication.primaryScreen()
        if canvas is None or not canvas.has_image() or screen is None:
            return
        image_size = canvas.image().size()
        available = screen.availableGeometry().size()
        side_width = self.left_toolbar.sizeHint().width() if self.left_toolbar.isVisible() else 0
        toolbar_height = sum(
            toolbar.sizeHint().height()
            for toolbar in (self.main_toolbar, self.properties_toolbar)
            if toolbar.isVisible()
        )
        chrome_width = side_width + 48
        chrome_height = self.menuBar().sizeHint().height() + toolbar_height + self.statusBar().sizeHint().height() + 96
        max_width = max(480, int(available.width() * 0.95))
        max_height = max(320, int(available.height() * 0.95))
        desired_width = min(max(480, image_size.width() + chrome_width), max_width)
        desired_height = min(max(320, image_size.height() + chrome_height), max_height)
        self.resize(desired_width, desired_height)

    def open_recent_image(self, path: str) -> None:
        if not Path(path).exists():
            self._remove_recent_image_path(path)
            self._show_error(f"Recent image no longer exists: {path}")
            return
        self._open_image_path(path)

    def clear_recent_images(self) -> None:
        self._recent_image_paths.clear()
        self._settings.remove("recent_images")
        self._update_actions()

    def _populate_recent_images_menu(self) -> None:
        self.recent_images_menu.clear()
        for index, path in enumerate(self._recent_image_paths[: self.MAX_RECENT_IMAGES], start=1):
            action = QAction(path, self.recent_images_menu)
            if index < 10:
                action.setShortcut(f"Ctrl+{index}")
            action.triggered.connect(lambda checked=False, selected_path=path: self.open_recent_image(selected_path))
            self.recent_images_menu.addAction(action)
        if self._recent_image_paths:
            self.recent_images_menu.addSeparator()
            self.recent_images_menu.addAction(self.clear_recent_images_action)
        self.recent_images_menu.setEnabled(bool(self._recent_image_paths))

    def _store_recent_image_path(self, path: str) -> None:
        resolved = str(Path(path).expanduser())
        self._recent_image_paths = [item for item in self._recent_image_paths if item != resolved]
        self._recent_image_paths.insert(0, resolved)
        self._recent_image_paths = self._recent_image_paths[: self.MAX_RECENT_IMAGES]
        self._settings.setValue("recent_images/paths", self._recent_image_paths)
        self._settings.setValue("paths/last_image_dir", str(Path(resolved).parent))
        self._update_actions()

    def _remove_recent_image_path(self, path: str) -> None:
        resolved = str(Path(path).expanduser())
        if resolved not in self._recent_image_paths:
            return
        self._recent_image_paths = [item for item in self._recent_image_paths if item != resolved]
        self._settings.setValue("recent_images/paths", self._recent_image_paths)
        self._update_actions()

    def _load_recent_image_paths(self) -> list[str]:
        raw_paths = self._settings.value("recent_images/paths", [])
        if isinstance(raw_paths, str):
            return [raw_paths] if raw_paths else []
        if isinstance(raw_paths, (list, tuple)):
            return [str(path) for path in raw_paths if path]
        return []

    def _default_image_directory(self) -> str:
        if not self._setting_bool("saver/remember_directory", False):
            return str(Path.home())
        configured = self._settings.value("paths/last_image_dir", "")
        if isinstance(configured, str) and configured:
            return configured
        return str(Path.home())

    def _current_settings_data(self) -> SettingsData:
        return SettingsData(
            tool=self._current_tool(),
            pen_width=self.stroke_width.value(),
            font_family=self.font_family.currentFont().family(),
            font_point_size=self.font_size.value(),
            fill_mode=self._current_fill_mode_value(),
            opacity_percent=self.opacity.value(),
            bold=self.bold.isChecked(),
            italic=self.italic.isChecked(),
            rotate_watermark=self.rotate_watermark_action.isChecked(),
            capture_delay_seconds=self._setting_int("capture/delay_seconds", 0),
            capture_implicit_delay_ms=self._setting_int("capture/implicit_delay_ms", 200),
            capture_include_cursor=self._setting_bool("capture/include_cursor", True),
            force_generic_wayland=self._setting_bool("capture/force_generic_wayland", False),
            scale_generic_wayland=self._setting_bool("capture/scale_generic_wayland", False),
            hide_main_window_during_capture=self._setting_bool("capture/hide_main_window", True),
            show_main_window_after_capture=self._setting_bool("capture/show_main_window_after_capture", True),
            auto_copy_new_captures=self._setting_bool("capture/auto_copy_new_captures", False),
            application_remember_position=self._setting_bool("application/remember_position", True),
            application_auto_hide_tabs=self._setting_bool("application/auto_hide_tabs", False),
            application_capture_on_startup=self._setting_bool("application/capture_on_startup", False),
            application_auto_hide_docks=self._setting_bool("application/auto_hide_docks", False),
            application_auto_resize_to_content=self._setting_bool("application/auto_resize_to_content", True),
            application_single_instance=self._setting_bool("application/single_instance", True),
            application_resize_delay_ms=self._setting_int("application/resize_delay_ms", 10),
            application_language=str(self._settings.value("application/language", "")),
            saver_prompt_discard=self._setting_bool("saver/prompt_discard", True),
            saver_remember_directory=self._setting_bool("saver/remember_directory", False),
            saver_quality_enabled=self._setting_bool("saver/quality_enabled", False),
            saver_quality_factor=self._setting_int("saver/quality_factor", 50),
            saver_auto_save=self._setting_bool("saver/auto_save", False),
            saver_location=str(self._settings.value("saver/location", str(Path.home() / "Pictures" / "$Y$M$D-$T.png"))),
            saver_overwrite=self._setting_bool("saver/overwrite", False),
            use_tray_icon=self._setting_bool("tray/use", True),
            minimize_to_tray=self._setting_bool("tray/minimize", True),
            close_to_tray=self._setting_bool("tray/close", True),
            start_minimized_to_tray=self._setting_bool("tray/start_minimized", False),
            tray_notifications=self._setting_bool("tray/notifications", True),
            tray_default_action=str(self._settings.value("tray/default_action", "show")),
            tray_default_capture_mode=str(self._settings.value("tray/default_capture_mode", "rect")),
            shortcuts_enabled=self._setting_bool("shortcuts/enabled", True),
            shortcuts={key: sequence.toString(QKeySequence.SequenceFormat.NativeText) for key, sequence in self._current_shortcuts().items()},
            upload_confirm_before_uploading=self._setting_bool("upload/confirm", False),
            upload_script_path=str(self._settings.value("upload/script_path", "")),
            upload_copy_output=self._setting_bool("upload/copy_output", False),
            upload_output_filter=str(self._settings.value("upload/output_filter", "")),
            upload_stop_on_stderr=self._setting_bool("upload/stop_on_stderr", False),
            ocr_enabled=self._setting_bool("ocr/enabled", True),
            ocr_backend=str(self._settings.value("ocr/backend", "paddleocr")),
            ocr_language=str(self._settings.value("ocr/language", "english")),
            ocr_copy_to_clipboard=self._setting_bool("ocr/copy_to_clipboard", False),
            ocr_script_path=str(self._settings.value("ocr/script_path", "")),
            spellcheck_scheme=[
                (
                    name,
                    fill.name(QColor.NameFormat.HexRgb),
                    underline.name(QColor.NameFormat.HexRgb),
                )
                for name, fill, underline in load_spellcheck_scheme(self._settings)
            ],
        )

    def _current_tool(self) -> Tool:
        for tool, action in (
            (Tool.SELECT, self.select_action),
            (Tool.PEN, self.pen_action),
            (Tool.MARKER_PEN, self.marker_pen_action),
            (Tool.LINE, self.line_action),
            (Tool.ARROW, self.arrow_action),
            (Tool.DOUBLE_ARROW, self.double_arrow_action),
            (Tool.RECT, self.rect_action),
            (Tool.ELLIPSE, self.ellipse_action),
            (Tool.MARKER_RECT, self.marker_rect_action),
            (Tool.MARKER_ELLIPSE, self.marker_ellipse_action),
            (Tool.TEXT, self.text_action),
            (Tool.TEXT_POINTER, self.text_pointer_action),
            (Tool.TEXT_ARROW, self.text_arrow_action),
            (Tool.NUMBER, self.number_action),
            (Tool.NUMBER_POINTER, self.number_pointer_action),
            (Tool.NUMBER_ARROW, self.number_arrow_action),
            (Tool.BLUR, self.blur_action),
            (Tool.PIXELATE, self.pixelate_action),
            (Tool.STICKER, self.sticker_action),
            (Tool.CROP, self.crop_action),
        ):
            if action.isChecked():
                return tool
        return Tool.SELECT

    def _apply_settings_data(self, data: SettingsData) -> None:
        self._settings.setValue("editor/tool", data.tool.value)
        self._settings.setValue("editor/pen_width", data.pen_width)
        self._settings.setValue("editor/font_family", data.font_family)
        self._settings.setValue("editor/font_point_size", data.font_point_size)
        self._settings.setValue("editor/fill_mode", data.fill_mode.value)
        self._settings.setValue("editor/opacity_percent", data.opacity_percent)
        self._settings.setValue("editor/bold", data.bold)
        self._settings.setValue("editor/italic", data.italic)
        self._settings.setValue("watermark/rotate", data.rotate_watermark)
        self._settings.setValue("capture/delay_seconds", data.capture_delay_seconds)
        self._settings.setValue("capture/implicit_delay_ms", data.capture_implicit_delay_ms)
        self._settings.setValue("capture/include_cursor", data.capture_include_cursor)
        self._settings.setValue("capture/force_generic_wayland", data.force_generic_wayland)
        self._settings.setValue("capture/scale_generic_wayland", data.scale_generic_wayland)
        self._settings.setValue("capture/hide_main_window", data.hide_main_window_during_capture)
        self._settings.setValue("capture/show_main_window_after_capture", data.show_main_window_after_capture)
        self._settings.setValue("capture/auto_copy_new_captures", data.auto_copy_new_captures)
        self._settings.setValue("application/remember_position", data.application_remember_position)
        self._settings.setValue("application/auto_hide_tabs", data.application_auto_hide_tabs)
        self._settings.setValue("application/capture_on_startup", data.application_capture_on_startup)
        self._settings.setValue("application/auto_hide_docks", data.application_auto_hide_docks)
        self._settings.setValue("application/auto_resize_to_content", data.application_auto_resize_to_content)
        self._settings.setValue("application/single_instance", data.application_single_instance)
        self._settings.setValue("application/resize_delay_ms", data.application_resize_delay_ms)
        self._settings.setValue("application/language", data.application_language)
        if not data.application_remember_position:
            self._settings.remove("window/geometry")
        self.tabs.tabBar().setAutoHide(data.application_auto_hide_tabs)
        self._settings.setValue("saver/prompt_discard", data.saver_prompt_discard)
        self._settings.setValue("saver/remember_directory", data.saver_remember_directory)
        self._settings.setValue("saver/quality_enabled", data.saver_quality_enabled)
        self._settings.setValue("saver/quality_factor", data.saver_quality_factor)
        self._settings.setValue("saver/auto_save", data.saver_auto_save)
        self._settings.setValue("saver/location", data.saver_location)
        self._settings.setValue("saver/overwrite", data.saver_overwrite)
        self._settings.setValue("tray/use", data.use_tray_icon)
        self._settings.setValue("tray/minimize", data.minimize_to_tray)
        self._settings.setValue("tray/close", data.close_to_tray)
        self._settings.setValue("tray/start_minimized", data.start_minimized_to_tray)
        self._settings.setValue("tray/notifications", data.tray_notifications)
        self._settings.setValue("tray/default_action", data.tray_default_action)
        self._settings.setValue("tray/default_capture_mode", data.tray_default_capture_mode)
        self._settings.setValue("shortcuts/enabled", data.shortcuts_enabled)
        for key, value in data.shortcuts.items():
            self._settings.setValue(f"shortcuts/{key}", value)
        self._settings.setValue("upload/confirm", data.upload_confirm_before_uploading)
        self._settings.setValue("upload/script_path", data.upload_script_path)
        self._settings.setValue("upload/copy_output", data.upload_copy_output)
        self._settings.setValue("upload/output_filter", data.upload_output_filter)
        self._settings.setValue("upload/stop_on_stderr", data.upload_stop_on_stderr)
        self._settings.setValue("ocr/enabled", data.ocr_enabled)
        self._settings.setValue("ocr/backend", data.ocr_backend)
        self._settings.setValue("ocr/language", data.ocr_language)
        self._settings.setValue("ocr/copy_to_clipboard", data.ocr_copy_to_clipboard)
        self._settings.setValue("ocr/script_path", data.ocr_script_path)
        save_spellcheck_scheme(
            [(name, QColor(fill), QColor(underline)) for name, fill, underline in data.spellcheck_scheme],
            self._settings,
        )

        self.capture_delay_toolbar.blockSignals(True)
        self.capture_delay_toolbar.setValue(data.capture_delay_seconds)
        self.capture_delay_toolbar.blockSignals(False)

        self.stroke_width.blockSignals(True)
        self.stroke_width.setValue(data.pen_width)
        self.stroke_width.blockSignals(False)

        self.font_family.blockSignals(True)
        self.font_family.setCurrentFont(QFont(data.font_family))
        self.font_family.blockSignals(False)

        self.font_size.blockSignals(True)
        self.font_size.setValue(data.font_point_size)
        self.font_size.blockSignals(False)

        fill_mode_index = self.fill_mode.findData(data.fill_mode)
        if fill_mode_index >= 0:
            self.fill_mode.blockSignals(True)
            self.fill_mode.setCurrentIndex(fill_mode_index)
            self.fill_mode.blockSignals(False)
        self._sync_fill_mode_button()
        self._sync_auxiliary_property_controls()

        self.opacity.blockSignals(True)
        self.opacity.setValue(data.opacity_percent)
        self.opacity.blockSignals(False)

        self.bold.blockSignals(True)
        self.bold.setChecked(data.bold)
        self.bold.blockSignals(False)

        self.italic.blockSignals(True)
        self.italic.setChecked(data.italic)
        self.italic.blockSignals(False)
        self.underline_button.setChecked(self._setting_bool("editor/underline", False))
        self.shadow_state_button.setChecked(self._setting_bool("editor/shadow_enabled", True))
        self.scaling.setValue(self._setting_int("editor/scaling_percent", 100))

        self.rotate_watermark_action.blockSignals(True)
        self.rotate_watermark_action.setChecked(data.rotate_watermark)
        self.rotate_watermark_action.blockSignals(False)

        self._apply_shortcuts_from_mapping(data.shortcuts)
        self.set_tool(data.tool)
        self._apply_defaults_to_canvases(data)
        self._apply_tray_settings()

    def _apply_defaults_to_canvases(self, data: SettingsData) -> None:
        sticker_paths = self._default_sticker_paths()
        for index in range(self.tabs.count()):
            canvas = self._canvas_from_tab_widget(self.tabs.widget(index))
            if canvas is None:
                continue
            canvas.set_pen_width(data.pen_width)
            canvas.set_text_color(QColor("#ffffff"))
            canvas.set_font_family(data.font_family)
            canvas.set_font_point_size(data.font_point_size)
            canvas.set_fill_mode(data.fill_mode)
            canvas.set_opacity(data.opacity_percent / 100.0)
            canvas.set_bold(data.bold)
            canvas.set_italic(data.italic)
            canvas.set_underline(self.underline_button.isChecked())
            canvas.set_shadow(self.shadow_state_button.isChecked())
            canvas.set_scaling(self.scaling.value() / 100.0)
            canvas.set_number_seed(self.number_value.value())
            canvas.set_sticker_paths(sticker_paths)
            if sticker_paths and canvas.sticker_path() is None:
                canvas.set_sticker_path(sticker_paths[0])

    def _restore_ui_settings(self) -> None:
        if self._setting_bool("application/remember_position", True):
            geometry = self._settings.value("window/geometry")
            if geometry is not None:
                self.restoreGeometry(geometry)
        self.tabs.tabBar().setAutoHide(self._setting_bool("application/auto_hide_tabs", False))
        self._set_docks_collapsed(self._setting_bool("application/auto_hide_docks", False))

        self.stroke_width.setValue(self._setting_int("editor/pen_width", 3))
        self.font_size.setValue(self._setting_int("editor/font_point_size", 14))
        self.opacity.setValue(self._setting_int("editor/opacity_percent", 100))
        self.bold.setChecked(self._setting_bool("editor/bold", False))
        self.italic.setChecked(self._setting_bool("editor/italic", False))
        self.underline_button.setChecked(self._setting_bool("editor/underline", False))
        self.shadow_state_button.setChecked(self._setting_bool("editor/shadow_enabled", True))
        self.scaling.setValue(self._setting_int("editor/scaling_percent", 100))
        self.number_value.setValue(self._setting_int("editor/number_seed", 1))

        stored_font_family = self._settings.value("editor/font_family", "")
        if isinstance(stored_font_family, str) and stored_font_family:
            self.font_family.setCurrentFont(QFont(stored_font_family))

        stored_fill_mode = self._settings.value("editor/fill_mode", FillMode.BORDER_AND_FILL.value)
        legacy_map = {
            "stroke_only": FillMode.BORDER_AND_NO_FILL,
            "fill_only": FillMode.NO_BORDER_AND_FILL,
            "stroke_and_fill": FillMode.BORDER_AND_FILL,
        }
        if stored_fill_mode in legacy_map:
            fill_mode = legacy_map[stored_fill_mode]
        else:
            fill_mode = FillMode(stored_fill_mode) if stored_fill_mode in {mode.value for mode in FillMode} else FillMode.BORDER_AND_FILL
        fill_mode_index = self.fill_mode.findData(fill_mode)
        if fill_mode_index >= 0:
            self.fill_mode.setCurrentIndex(fill_mode_index)
        self._sync_fill_mode_button()
        self._sync_auxiliary_property_controls()

    def _apply_tray_settings(self) -> None:
        if self._tray_icon is None:
            return
        if self._setting_bool("tray/use", True):
            self._tray_icon.show()
        else:
            self._tray_icon.hide()

    def _apply_tool_selection_from_settings(self) -> None:
        stored_tool = self._settings.value("editor/tool", Tool.SELECT.value)
        try:
            tool = Tool(stored_tool)
        except ValueError:
            tool = Tool.SELECT
        if tool == Tool.CUT:
            tool = Tool.SELECT
        self.set_tool(tool)

    def _shortcut_defaults(self) -> dict[str, QKeySequence]:
        return {
            "capture_rect": QKeySequence("Ctrl+Shift+R"),
            "capture_last_rect": QKeySequence("Ctrl+Shift+L"),
            "capture_full": QKeySequence("Ctrl+Shift+F"),
            "capture_current": QKeySequence("Ctrl+Shift+S"),
            "capture_active": QKeySequence("Ctrl+Shift+A"),
            "capture_under_cursor": QKeySequence("Ctrl+Shift+U"),
            "capture_portal": QKeySequence("Alt+Shift+T"),
            "open": QKeySequence(QKeySequence.StandardKey.Open),
            "save": QKeySequence(QKeySequence.StandardKey.Save),
            "paste": QKeySequence(QKeySequence.StandardKey.Paste),
            "pin": QKeySequence("Ctrl+Shift+P"),
            "watermark": QKeySequence("Shift+W"),
            "upload": QKeySequence("Ctrl+Shift+U"),
            "ocr": QKeySequence("Ctrl+Shift+T"),
        }

    def _shortcut_actions(self) -> dict[str, QAction]:
        return {
            "capture_rect": self.new_capture_rect_action,
            "capture_last_rect": self.new_capture_last_rect_action,
            "capture_full": self.new_capture_full_action,
            "capture_current": self.new_capture_current_action,
            "capture_active": self.new_capture_active_action,
            "capture_under_cursor": self.new_capture_under_cursor_action,
            "capture_portal": self.new_capture_portal_action,
            "open": self.open_action,
            "save": self.save_action,
            "paste": self.paste_action,
            "pin": self.pin_action,
            "watermark": self.add_watermark_action,
            "upload": self.upload_action,
            "ocr": self.ocr_action,
        }

    def _current_shortcuts(self) -> dict[str, QKeySequence]:
        return {key: action.shortcut() for key, action in self._shortcut_actions().items()}

    def _apply_shortcuts(self) -> None:
        mapping: dict[str, str] = {}
        for key, default_sequence in self._shortcut_defaults().items():
            stored = self._settings.value(f"shortcuts/{key}", default_sequence.toString(QKeySequence.SequenceFormat.NativeText))
            mapping[key] = str(stored) if stored is not None else ""
        self._apply_shortcuts_from_mapping(mapping)

    def _apply_shortcuts_from_mapping(self, mapping: dict[str, str]) -> None:
        defaults = self._shortcut_defaults()
        shortcuts_enabled = self._setting_bool("shortcuts/enabled", True)
        for key, action in self._shortcut_actions().items():
            value = mapping.get(key, defaults[key].toString(QKeySequence.SequenceFormat.NativeText))
            action.setShortcut(QKeySequence(value) if value and shortcuts_enabled else QKeySequence())

    def _save_ui_settings(self) -> None:
        if self._setting_bool("application/remember_position", True):
            self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("editor/pen_width", self.stroke_width.value())
        self._settings.setValue("editor/font_family", self.font_family.currentFont().family())
        self._settings.setValue("editor/font_point_size", self.font_size.value())
        self._settings.setValue("editor/opacity_percent", self.opacity.value())
        self._settings.setValue("editor/fill_mode", self._current_fill_mode_value().value)
        self._settings.setValue("editor/bold", self.bold.isChecked())
        self._settings.setValue("editor/italic", self.italic.isChecked())
        self._settings.setValue("editor/underline", self.underline_button.isChecked())
        self._settings.setValue("editor/shadow_enabled", self.shadow_state_button.isChecked())
        self._settings.setValue("editor/scaling_percent", self.scaling.value())
        self._settings.setValue("editor/number_seed", self.number_value.value())

    def _should_minimize_to_tray(self) -> bool:
        return (
            self._tray_icon is not None
            and self._tray_icon.isVisible()
            and self._setting_bool("tray/use", True)
            and self._setting_bool("tray/minimize", True)
        )

    def _should_close_to_tray(self) -> bool:
        return (
            not self._allow_quit
            and self._tray_icon is not None
            and self._tray_icon.isVisible()
            and self._setting_bool("tray/use", True)
            and self._setting_bool("tray/close", True)
        )

    def _tray_capture_action(self) -> QAction:
        mode = str(self._settings.value("tray/default_capture_mode", "rect"))
        return {
            "rect": self.new_capture_rect_action,
            "last_rect": self.new_capture_last_rect_action,
            "full": self.new_capture_full_action,
            "current": self.new_capture_current_action,
            "active": self.new_capture_active_action,
            "under_cursor": self.new_capture_under_cursor_action,
            "portal": self.new_capture_portal_action,
        }.get(mode, self.new_capture_rect_action)

    def _trigger_tray_default_action(self) -> None:
        action = str(self._settings.value("tray/default_action", "show"))
        if action == "capture":
            self._tray_capture_action().trigger()
            return
        self.show_from_tray()

    def _handle_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason != QSystemTrayIcon.ActivationReason.Context:
            self._trigger_tray_default_action()

    def close_other_pin_windows(self, current_window: PinWindow) -> None:
        for pin_window in list(self._pin_windows):
            if pin_window is not current_window:
                pin_window.close()

    def close_all_pin_windows(self) -> None:
        for pin_window in list(self._pin_windows):
            pin_window.close()

    def _forget_pin_window(self, window: PinWindow) -> None:
        self._pin_windows = [pin_window for pin_window in self._pin_windows if pin_window is not window]

    def _setting_int(self, key: str, default: int) -> int:
        value = self._settings.value(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _setting_bool(self, key: str, default: bool) -> bool:
        value = self._settings.value(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _confirm_discard_canvas(self, canvas: AnnotationCanvas) -> bool:
        if not canvas.state.dirty or not self._setting_bool("saver/prompt_discard", True):
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved changes",
            "Close this tab and discard unsaved changes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _confirm_close_all_tabs(self) -> bool:
        if not self._setting_bool("saver/prompt_discard", True):
            return True
        dirty_canvases = []
        for index in range(self.tabs.count()):
            canvas = self._canvas_from_tab_widget(self.tabs.widget(index))
            if canvas is not None and canvas.state.dirty:
                dirty_canvases.append(canvas)
        if not dirty_canvases:
            return True
        reply = QMessageBox.question(
            self,
            "Unsaved changes",
            "Close ksnip PyQt6 and discard unsaved changes in open tabs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "ksnip PyQt6", message)

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "PyQt6 MVP port of ksnip.\n\nImplemented: capture, tabs, open/save/copy, script upload, experimental OCR, annotation tools, image overlays, watermarking, item properties, multi-selection editing, persistence, settings dialog, configurable app hotkeys, tray workflow, and pin windows.",
        )
