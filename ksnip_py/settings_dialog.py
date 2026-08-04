from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from .canvas import FillMode, Tool
from .spellcheck import default_spellcheck_scheme, load_spellcheck_scheme
from .watermark import WatermarkStore


@dataclass
class SettingsData:
    tool: Tool
    pen_width: int
    font_family: str
    font_point_size: int
    fill_mode: FillMode
    opacity_percent: int
    bold: bool
    italic: bool
    rotate_watermark: bool
    capture_delay_seconds: int
    capture_implicit_delay_ms: int
    capture_include_cursor: bool
    force_generic_wayland: bool
    scale_generic_wayland: bool
    hide_main_window_during_capture: bool
    show_main_window_after_capture: bool
    auto_copy_new_captures: bool
    application_remember_position: bool
    application_auto_hide_tabs: bool
    application_capture_on_startup: bool
    application_auto_hide_docks: bool
    application_auto_resize_to_content: bool
    application_single_instance: bool
    application_resize_delay_ms: int
    application_language: str
    saver_prompt_discard: bool
    saver_remember_directory: bool
    saver_quality_enabled: bool
    saver_quality_factor: int
    saver_auto_save: bool
    saver_location: str
    saver_overwrite: bool
    use_tray_icon: bool
    minimize_to_tray: bool
    close_to_tray: bool
    start_minimized_to_tray: bool
    tray_notifications: bool
    tray_default_action: str
    tray_default_capture_mode: str
    shortcuts_enabled: bool
    shortcuts: dict[str, str]
    upload_confirm_before_uploading: bool
    upload_script_path: str
    upload_copy_output: bool
    upload_output_filter: str
    upload_stop_on_stderr: bool
    ocr_enabled: bool
    ocr_backend: str
    ocr_language: str
    ocr_copy_to_clipboard: bool
    ocr_script_path: str
    spellcheck_scheme: list[tuple[str, str, str]]


class SettingsDialog(QDialog):
    def __init__(self, initial: SettingsData, watermark_store: WatermarkStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._watermark_store = watermark_store
        self.setWindowTitle(self.tr("Settings"))
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout, 1)

        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText(self.tr("Search Settings..."))
        self.navigation_tree = QTreeWidget(self)
        self.navigation_tree.setHeaderHidden(True)
        self.navigation_tree.setFixedWidth(170)
        self.navigation_tree.currentItemChanged.connect(self._show_settings_page)
        self.search_line_edit.textChanged.connect(self._filter_navigation_items)
        self._navigation_items: dict[str, QTreeWidgetItem] = {}
        self._navigation_order: list[QTreeWidgetItem] = []

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_line_edit)
        left_layout.addWidget(self.navigation_tree, 1)

        left_host = QWidget(self)
        left_host.setLayout(left_layout)
        content_layout.addWidget(left_host)

        self.page_stack = QStackedWidget(self)
        content_layout.addWidget(self.page_stack, 1)

        editor_group = QGroupBox(self.tr("Editor Defaults"), self)
        editor_layout = QFormLayout(editor_group)

        self.tool_combo = QComboBox(editor_group)
        self.tool_combo.addItem(self.tr("Select"), Tool.SELECT)
        self.tool_combo.addItem(self.tr("Pen"), Tool.PEN)
        self.tool_combo.addItem(self.tr("Marker Pen"), Tool.MARKER_PEN)
        self.tool_combo.addItem(self.tr("Line"), Tool.LINE)
        self.tool_combo.addItem(self.tr("Arrow"), Tool.ARROW)
        self.tool_combo.addItem(self.tr("Double Arrow"), Tool.DOUBLE_ARROW)
        self.tool_combo.addItem(self.tr("Rectangle"), Tool.RECT)
        self.tool_combo.addItem(self.tr("Ellipse"), Tool.ELLIPSE)
        self.tool_combo.addItem(self.tr("Marker Rectangle"), Tool.MARKER_RECT)
        self.tool_combo.addItem(self.tr("Marker Ellipse"), Tool.MARKER_ELLIPSE)
        self.tool_combo.addItem(self.tr("Text"), Tool.TEXT)
        self.tool_combo.addItem(self.tr("Text Pointer"), Tool.TEXT_POINTER)
        self.tool_combo.addItem(self.tr("Text Arrow"), Tool.TEXT_ARROW)
        self.tool_combo.addItem(self.tr("Number"), Tool.NUMBER)
        self.tool_combo.addItem(self.tr("Number Pointer"), Tool.NUMBER_POINTER)
        self.tool_combo.addItem(self.tr("Number Arrow"), Tool.NUMBER_ARROW)
        self.tool_combo.addItem(self.tr("Blur"), Tool.BLUR)
        self.tool_combo.addItem(self.tr("Pixelate"), Tool.PIXELATE)
        self.tool_combo.addItem(self.tr("Sticker"), Tool.STICKER)
        self.tool_combo.addItem(self.tr("Crop"), Tool.CROP)
        editor_layout.addRow(self.tr("Default Tool"), self.tool_combo)

        self.pen_width = QSpinBox(editor_group)
        self.pen_width.setRange(1, 20)
        editor_layout.addRow(self.tr("Stroke Width"), self.pen_width)

        self.font_family = QFontComboBox(editor_group)
        editor_layout.addRow(self.tr("Font Family"), self.font_family)

        self.font_size = QSpinBox(editor_group)
        self.font_size.setRange(6, 144)
        editor_layout.addRow(self.tr("Font Size"), self.font_size)

        self.fill_mode = QComboBox(editor_group)
        self.fill_mode.addItem(self.tr("Border and Fill"), FillMode.BORDER_AND_FILL)
        self.fill_mode.addItem(self.tr("Border and No Fill"), FillMode.BORDER_AND_NO_FILL)
        self.fill_mode.addItem(self.tr("No Border and No Fill"), FillMode.NO_BORDER_AND_NO_FILL)
        editor_layout.addRow(self.tr("Shape Fill Mode"), self.fill_mode)

        self.opacity = QSpinBox(editor_group)
        self.opacity.setRange(0, 100)
        editor_layout.addRow(self.tr("Opacity %"), self.opacity)

        style_row = QHBoxLayout()
        self.bold = QCheckBox(self.tr("Bold"), editor_group)
        self.italic = QCheckBox(self.tr("Italic"), editor_group)
        style_row.addWidget(self.bold)
        style_row.addWidget(self.italic)
        style_host = QWidget(editor_group)
        style_host.setLayout(style_row)
        editor_layout.addRow(self.tr("Text Style"), style_host)

        watermark_group = QGroupBox(self.tr("Watermark"), self)
        watermark_layout = QFormLayout(watermark_group)

        self.rotate_watermark = QCheckBox(self.tr("Rotate Watermark 45°"), watermark_group)
        watermark_layout.addRow(self.rotate_watermark)

        image_row = QHBoxLayout()
        self.watermark_status = QLabel(watermark_group)
        self.update_watermark_button = QPushButton(self.tr("Update Image..."), watermark_group)
        self.update_watermark_button.clicked.connect(self._update_watermark_image)
        image_row.addWidget(self.watermark_status, 1)
        image_row.addWidget(self.update_watermark_button)
        image_host = QWidget(watermark_group)
        image_host.setLayout(image_row)
        watermark_layout.addRow(self.tr("Stored Image"), image_host)

        application_group = QGroupBox(self.tr("Application"), self)
        application_layout = QVBoxLayout(application_group)

        self.auto_copy_new_captures = QCheckBox(self.tr("Automatically copy new captures to clipboard"), application_group)
        application_layout.addWidget(self.auto_copy_new_captures)

        self.remember_window_position = QCheckBox(self.tr("Remember Main Window position on move and load on startup"), application_group)
        application_layout.addWidget(self.remember_window_position)

        self.capture_on_startup = QCheckBox(self.tr("Capture screenshot at startup with default mode"), application_group)
        application_layout.addWidget(self.capture_on_startup)

        self.use_tabs = QCheckBox(self.tr("Use Tabs"), application_group)
        self.use_tabs.setChecked(True)
        self.use_tabs.setEnabled(False)
        application_layout.addWidget(self.use_tabs)

        self.auto_hide_tabs = QCheckBox(self.tr("Auto hide Tabs"), application_group)
        application_layout.addWidget(self.auto_hide_tabs)

        self.run_single_instance = QCheckBox(self.tr("Run ksnip as single instance"), application_group)
        application_layout.addWidget(self.run_single_instance)

        self.auto_hide_docks = QCheckBox(self.tr("Auto hide Docks"), application_group)
        application_layout.addWidget(self.auto_hide_docks)

        self.auto_resize_to_content = QCheckBox(self.tr("Auto resize to content"), application_group)
        application_layout.addWidget(self.auto_resize_to_content)

        self.enable_debugging = QCheckBox(self.tr("Enable Debugging"), application_group)
        self.enable_debugging.setEnabled(False)
        application_layout.addWidget(self.enable_debugging)

        application_details_group = QGroupBox(self.tr("Appearance and Paths"), self)
        application_details_layout = QFormLayout(application_details_group)

        self.resize_delay = QSpinBox(application_details_group)
        self.resize_delay.setRange(0, 1000)
        self.resize_delay.setSuffix(" ms")
        self.resize_delay.setValue(10)
        application_details_layout.addRow(self.tr("Resize delay"), self.resize_delay)

        self.application_language = QComboBox(application_details_group)
        self.application_language.addItem(self.tr("System default"), "")
        self.application_language.addItem(self.tr("English"), "en")
        self.application_language.addItem(self.tr("Spanish"), "es")
        application_details_layout.addRow(self.tr("Language"), self.application_language)

        self.application_style = QComboBox(application_details_group)
        self.application_style.addItems(["Fusion", "Windows"])
        self.application_style.setEnabled(False)
        application_details_layout.addRow(self.tr("Application Style"), self.application_style)

        temp_directory_row = QHBoxLayout()
        self.temp_directory = QLineEdit("/tmp", application_details_group)
        self.temp_directory.setEnabled(False)
        self.temp_directory_browse = QPushButton(self.tr("Browse"), application_details_group)
        self.temp_directory_browse.setEnabled(False)
        temp_directory_row.addWidget(self.temp_directory, 1)
        temp_directory_row.addWidget(self.temp_directory_browse)
        temp_directory_host = QWidget(application_details_group)
        temp_directory_host.setLayout(temp_directory_row)
        application_details_layout.addRow(self.tr("Temp Directory"), temp_directory_host)

        capture_group = QGroupBox(self.tr("Capture"), self)
        capture_layout = QFormLayout(capture_group)

        self.capture_delay_seconds = QSpinBox(capture_group)
        self.capture_delay_seconds.setRange(0, 60)
        self.capture_delay_seconds.setSuffix(" s")
        capture_layout.addRow(self.tr("Capture Delay"), self.capture_delay_seconds)

        self.hide_main_window_during_capture = QCheckBox(self.tr("Hide Main Window During Capture"), capture_group)
        self.show_main_window_after_capture = QCheckBox(self.tr("Show Main Window After Capture"), capture_group)
        capture_layout.addRow(self.hide_main_window_during_capture)
        capture_layout.addRow(self.show_main_window_after_capture)

        saver_group = QGroupBox(self.tr("Saver"), self)
        saver_layout = QVBoxLayout(saver_group)
        self.saver_auto_save = QCheckBox(self.tr("Automatically save new captures to default location"), saver_group)
        self.saver_prompt_discard = QCheckBox(self.tr("Prompt to save before discarding unsaved changes"), saver_group)
        self.saver_remember_directory = QCheckBox(self.tr("Remember last Save Directory"), saver_group)
        saver_layout.addWidget(self.saver_auto_save)
        saver_layout.addWidget(self.saver_prompt_discard)
        saver_layout.addWidget(self.saver_remember_directory)

        saver_quality_group = QGroupBox(self.tr("Save Quality"), self)
        saver_quality_layout = QVBoxLayout(saver_quality_group)
        self.saver_quality_default = QRadioButton(self.tr("Default"), saver_quality_group)
        self.saver_quality_default.setChecked(True)
        self.saver_quality_factor = QRadioButton(self.tr("Factor"), saver_quality_group)
        self.saver_quality_value = QSpinBox(saver_quality_group)
        self.saver_quality_value.setRange(0, 100)
        self.saver_quality_value.setValue(50)
        self.saver_quality_factor.toggled.connect(self.saver_quality_value.setEnabled)
        quality_factor_row = QHBoxLayout()
        quality_factor_row.addWidget(self.saver_quality_factor)
        quality_factor_row.addWidget(self.saver_quality_value)
        quality_factor_row.addStretch(1)
        saver_quality_layout.addWidget(self.saver_quality_default)
        saver_quality_layout.addLayout(quality_factor_row)

        saver_location_group = QGroupBox(self.tr("Capture save location and filename"), self)
        saver_location_layout = QVBoxLayout(saver_location_group)
        self.saver_location = QLineEdit(saver_location_group)
        self.saver_location.setToolTip(self.tr("Supports $Y, $M, $D, $h, $m, $s, $T and consecutive # characters as a counter."))
        self.saver_location_browse = QPushButton(self.tr("Browse..."), saver_location_group)
        self.saver_location_browse.clicked.connect(self._select_saver_location)
        saver_location_row = QHBoxLayout()
        saver_location_row.addWidget(self.saver_location, 1)
        saver_location_row.addWidget(self.saver_location_browse)
        self.saver_overwrite = QCheckBox(self.tr("Overwrite file with same name"), saver_location_group)
        saver_location_layout.addLayout(saver_location_row)
        saver_location_layout.addWidget(self.saver_overwrite)

        image_grabber_group = QGroupBox(self.tr("Image Grabber"), self)
        image_grabber_layout = QVBoxLayout(image_grabber_group)
        self.capture_mouse_cursor = QCheckBox(self.tr("Capture mouse cursor on screenshot"), image_grabber_group)
        self.show_main_window_after_capture_checkbox = QCheckBox(self.tr("Show Main Window after capturing screenshot"), image_grabber_group)
        self.show_main_window_after_capture_checkbox.setChecked(True)
        self.hide_main_window_during_capture_checkbox = QCheckBox(self.tr("Hide Main Window during screenshot"), image_grabber_group)
        self.hide_main_window_during_capture_checkbox.setChecked(True)
        self.force_generic_wayland = QCheckBox(self.tr("Force Generic Wayland (xdg-desktop-portal) Screenshot"), image_grabber_group)
        self.scale_generic_wayland = QCheckBox(self.tr("Scale Generic Wayland (xdg-desktop-portal) Screenshots"), image_grabber_group)
        image_grabber_layout.addWidget(self.capture_mouse_cursor)
        image_grabber_layout.addWidget(self.show_main_window_after_capture_checkbox)
        image_grabber_layout.addWidget(self.hide_main_window_during_capture_checkbox)
        image_grabber_layout.addWidget(self.force_generic_wayland)
        image_grabber_layout.addWidget(self.scale_generic_wayland)

        image_grabber_delay_group = QGroupBox(self.tr("Delays"), self)
        image_grabber_delay_layout = QFormLayout(image_grabber_delay_group)
        self.implicit_capture_delay = QSpinBox(image_grabber_delay_group)
        self.implicit_capture_delay.setRange(0, 2000)
        self.implicit_capture_delay.setSuffix(" ms")
        self.implicit_capture_delay.setValue(200)
        self.implicit_capture_delay.setSingleStep(10)
        image_grabber_delay_layout.addRow(self.tr("Implicit capture delay"), self.implicit_capture_delay)

        snipping_area_group = QGroupBox(self.tr("Snipping Area"), self)
        snipping_area_layout = QVBoxLayout(snipping_area_group)
        self.freeze_image_while_snipping = QCheckBox(self.tr("Freeze Image while snipping"), snipping_area_group)
        self.freeze_image_while_snipping.setEnabled(False)
        self.show_magnifying_glass = QCheckBox(self.tr("Show magnifying glass on snipping area"), snipping_area_group)
        self.show_magnifying_glass.setEnabled(False)
        self.show_snipping_rulers = QCheckBox(self.tr("Show Snipping Area rulers"), snipping_area_group)
        self.show_snipping_rulers.setEnabled(False)
        self.show_snipping_position_size = QCheckBox(self.tr("Show Snipping Area position and size info"), snipping_area_group)
        self.show_snipping_position_size.setEnabled(False)
        self.allow_resizing_rect = QCheckBox(self.tr("Allow resizing rect area selection by default"), snipping_area_group)
        self.allow_resizing_rect.setEnabled(False)
        self.show_snipping_info_text = QCheckBox(self.tr("Show Snipping Area info text"), snipping_area_group)
        self.show_snipping_info_text.setEnabled(False)
        for widget in (
            self.freeze_image_while_snipping,
            self.show_magnifying_glass,
            self.show_snipping_rulers,
            self.show_snipping_position_size,
            self.allow_resizing_rect,
            self.show_snipping_info_text,
        ):
            snipping_area_layout.addWidget(widget)

        snipping_area_appearance_group = QGroupBox(self.tr("Appearance"), self)
        snipping_area_appearance_layout = QFormLayout(snipping_area_appearance_group)
        self.snipping_adorner_color = QLineEdit("#ff0000", snipping_area_appearance_group)
        self.snipping_adorner_color.setEnabled(False)
        self.snipping_cursor_color = QLineEdit("#221155", snipping_area_appearance_group)
        self.snipping_cursor_color.setEnabled(False)
        self.snipping_cursor_thickness = QSpinBox(snipping_area_appearance_group)
        self.snipping_cursor_thickness.setRange(1, 10)
        self.snipping_cursor_thickness.setValue(1)
        self.snipping_cursor_thickness.setEnabled(False)
        self.snipping_area_transparency = QSpinBox(snipping_area_appearance_group)
        self.snipping_area_transparency.setRange(0, 255)
        self.snipping_area_transparency.setValue(150)
        self.snipping_area_transparency.setEnabled(False)
        snipping_area_appearance_layout.addRow(self.tr("Snipping Area adorner color"), self.snipping_adorner_color)
        snipping_area_appearance_layout.addRow(self.tr("Snipping Area cursor color"), self.snipping_cursor_color)
        snipping_area_appearance_layout.addRow(self.tr("Snipping Area cursor thickness"), self.snipping_cursor_thickness)
        snipping_area_appearance_layout.addRow(self.tr("Snipping Area Transparency"), self.snipping_area_transparency)

        annotator_group = QGroupBox(self.tr("Annotator"), self)
        annotator_layout = QVBoxLayout(annotator_group)
        self.remember_annotation_tool = QCheckBox(self.tr("Remember annotation tool selection and load on startup"), annotator_group)
        self.remember_annotation_tool.setEnabled(False)
        self.switch_to_select_tool = QCheckBox(self.tr("Switch to Select Tool after drawing Item"), annotator_group)
        self.switch_to_select_tool.setEnabled(False)
        self.select_item_after_drawing = QCheckBox(self.tr("Select Item after drawing"), annotator_group)
        self.select_item_after_drawing.setEnabled(False)
        self.number_tool_seed_updates = QCheckBox(self.tr("Number Tool Seed change updates all Number Items"), annotator_group)
        self.number_tool_seed_updates.setEnabled(False)
        self.show_controls_widget = QCheckBox(self.tr("Show Controls Widget"), annotator_group)
        self.show_controls_widget.setEnabled(False)
        self.smooth_painter_paths = QCheckBox(self.tr("Smooth Painter Paths"), annotator_group)
        self.smooth_painter_paths.setEnabled(False)
        for widget in (
            self.remember_annotation_tool,
            self.switch_to_select_tool,
            self.select_item_after_drawing,
            self.number_tool_seed_updates,
            self.show_controls_widget,
            self.smooth_painter_paths,
        ):
            annotator_layout.addWidget(widget)

        annotator_appearance_group = QGroupBox(self.tr("Canvas"), self)
        annotator_appearance_layout = QFormLayout(annotator_appearance_group)
        self.smooth_factor = QSpinBox(annotator_appearance_group)
        self.smooth_factor.setRange(1, 20)
        self.smooth_factor.setValue(7)
        self.smooth_factor.setEnabled(False)
        self.canvas_color = QLineEdit("#ffffff", annotator_appearance_group)
        self.canvas_color.setEnabled(False)
        annotator_appearance_layout.addRow(self.tr("Smooth Factor"), self.smooth_factor)
        annotator_appearance_layout.addRow(self.tr("Canvas Color"), self.canvas_color)
        tray_group = QGroupBox(self.tr("Tray Icon"), self)
        tray_layout = QFormLayout(tray_group)

        self.use_tray_icon = QCheckBox(self.tr("Use Tray Icon"), tray_group)
        self.minimize_to_tray = QCheckBox(self.tr("Minimize To Tray"), tray_group)
        self.close_to_tray = QCheckBox(self.tr("Close To Tray"), tray_group)
        self.start_minimized_to_tray = QCheckBox(self.tr("Start Minimized To Tray"), tray_group)
        self.tray_notifications = QCheckBox(self.tr("Display Tray Notifications"), tray_group)
        tray_layout.addRow(self.use_tray_icon)
        tray_layout.addRow(self.minimize_to_tray)
        tray_layout.addRow(self.close_to_tray)
        tray_layout.addRow(self.start_minimized_to_tray)
        tray_layout.addRow(self.tray_notifications)
        self.use_tray_icon.toggled.connect(self._sync_tray_controls)

        tray_defaults_group = QGroupBox(self.tr("Default Action"), self)
        tray_defaults_layout = QFormLayout(tray_defaults_group)
        self.tray_default_action = QComboBox(tray_defaults_group)
        self.tray_default_action.addItem(self.tr("Show Editor"), "show")
        self.tray_default_action.addItem(self.tr("Capture"), "capture")
        tray_defaults_layout.addRow(self.tr("Action"), self.tray_default_action)

        self.tray_default_capture_mode = QComboBox(tray_defaults_group)
        self.tray_default_capture_mode.addItem(self.tr("Rect Area"), "rect")
        self.tray_default_capture_mode.addItem(self.tr("Last Rect Area"), "last_rect")
        self.tray_default_capture_mode.addItem(self.tr("Full Screen"), "full")
        self.tray_default_capture_mode.addItem(self.tr("Current Screen"), "current")
        self.tray_default_capture_mode.addItem(self.tr("Active Window"), "active")
        self.tray_default_capture_mode.addItem(self.tr("Window Under Cursor"), "under_cursor")
        self.tray_default_capture_mode.addItem(self.tr("Portal"), "portal")
        tray_defaults_layout.addRow(self.tr("Capture Mode"), self.tray_default_capture_mode)
        self.tray_default_action.currentIndexChanged.connect(self._sync_tray_default_controls)
        shortcuts_group = QGroupBox(self.tr("Global HotKeys"), self)
        shortcuts_layout = QFormLayout(shortcuts_group)
        self.enable_global_hotkeys = QCheckBox(self.tr("Enable Global HotKeys"), shortcuts_group)
        shortcuts_layout.addRow(self.enable_global_hotkeys)
        self.shortcut_edits: dict[str, QKeySequenceEdit] = {}
        self.shortcut_clear_buttons: list[QPushButton] = []
        for key, label in (
            ("capture_rect", self.tr("Rect Area Capture")),
            ("capture_last_rect", self.tr("Last Rect Area Capture")),
            ("capture_full", self.tr("Full Screen Capture")),
            ("capture_current", self.tr("Current Screen Capture")),
            ("capture_active", self.tr("Active Window Capture")),
            ("capture_under_cursor", self.tr("Window Under Cursor Capture")),
            ("capture_portal", self.tr("Portal Capture")),
            ("open", self.tr("Open Image")),
            ("save", self.tr("Save")),
            ("paste", self.tr("Paste Image")),
            ("pin", self.tr("Pin Image")),
            ("watermark", self.tr("Add Watermark")),
            ("upload", self.tr("Upload Image")),
            ("ocr", self.tr("OCR Text Recognition")),
        ):
            editor = QKeySequenceEdit(shortcuts_group)
            self.shortcut_edits[key] = editor
            clear_button = QPushButton(self.tr("Clear"), shortcuts_group)
            clear_button.clicked.connect(lambda _checked=False, target=editor: target.clear())
            self.shortcut_clear_buttons.append(clear_button)
            row_layout = QHBoxLayout()
            row_layout.addWidget(editor, 1)
            row_layout.addWidget(clear_button)
            row_host = QWidget(shortcuts_group)
            row_host.setLayout(row_layout)
            shortcuts_layout.addRow(label, row_host)
        self.enable_global_hotkeys.toggled.connect(self._sync_shortcut_controls)
        uploader_group = QGroupBox(self.tr("Uploader"), self)
        uploader_layout = QFormLayout(uploader_group)
        self.ask_confirmation_before_uploading = QCheckBox(self.tr("Ask for confirmation before uploading"), uploader_group)
        uploader_layout.addRow(self.ask_confirmation_before_uploading)
        self.uploader_type = QComboBox(uploader_group)
        self.uploader_type.addItem("Imgur", "imgur")
        self.uploader_type.addItem("FTP", "ftp")
        self.uploader_type.addItem(self.tr("Script"), "script")
        self.uploader_type.setEnabled(False)
        uploader_layout.addRow(self.tr("Uploader Type"), self.uploader_type)

        upload_group = QGroupBox(self.tr("Script Uploader"), self)
        upload_layout = QFormLayout(upload_group)
        script_row = QHBoxLayout()
        self.upload_script_path = QLineEdit(upload_group)
        self.upload_script_button = QPushButton(self.tr("Browse..."), upload_group)
        self.upload_script_button.clicked.connect(self._select_upload_script)
        script_row.addWidget(self.upload_script_path, 1)
        script_row.addWidget(self.upload_script_button)
        script_host = QWidget(upload_group)
        script_host.setLayout(script_row)
        upload_layout.addRow(self.tr("Script"), script_host)

        self.upload_copy_output = QCheckBox(self.tr("Copy script output to clipboard"), upload_group)
        upload_layout.addRow(self.upload_copy_output)

        self.upload_output_filter = QLineEdit(upload_group)
        upload_layout.addRow(self.tr("Filter"), self.upload_output_filter)

        self.upload_stop_on_stderr = QCheckBox(self.tr("Treat stderr as failure"), upload_group)
        upload_layout.addRow(self.upload_stop_on_stderr)
        ocr_group = QGroupBox(self.tr("OCR"), self)
        ocr_layout = QFormLayout(ocr_group)
        self.ocr_enabled = QCheckBox(self.tr("Enable OCR actions"), ocr_group)
        self.ocr_backend = QComboBox(ocr_group)
        self.ocr_backend.addItem("PaddleOCR", "paddleocr")
        self.ocr_backend.addItem(self.tr("Script"), "script")
        self.ocr_language = QComboBox(ocr_group)
        self.ocr_language.addItem(self.tr("English"), "english")
        self.ocr_language.addItem(self.tr("Spanish"), "spanish")
        self.ocr_language.addItem(self.tr("Spanish + English (script backend recommended)"), "spanish_english")
        self.ocr_copy_to_clipboard = QCheckBox(self.tr("Copy OCR result to clipboard automatically"), ocr_group)
        ocr_script_row = QHBoxLayout()
        self.ocr_script_path = QLineEdit(ocr_group)
        self.ocr_script_button = QPushButton(self.tr("Browse..."), ocr_group)
        self.ocr_script_button.clicked.connect(self._select_ocr_script)
        ocr_script_row.addWidget(self.ocr_script_path, 1)
        ocr_script_row.addWidget(self.ocr_script_button)
        ocr_script_host = QWidget(ocr_group)
        ocr_script_host.setLayout(ocr_script_row)
        ocr_layout.addRow(self.ocr_enabled)
        ocr_layout.addRow(self.tr("Backend"), self.ocr_backend)
        ocr_layout.addRow(self.tr("Language"), self.ocr_language)
        ocr_layout.addRow(self.ocr_copy_to_clipboard)
        ocr_layout.addRow(self.tr("Script Path"), ocr_script_host)
        self.ocr_enabled.toggled.connect(self._sync_ocr_controls)
        self.ocr_backend.currentIndexChanged.connect(self._sync_ocr_controls)

        scheme_group = QGroupBox(self.tr("Color scheme for misspelled words"), self)
        scheme_layout = QVBoxLayout(scheme_group)
        hint = self.tr("%1 base scheme colors used by the Text tool fill color on the left and the underline color for misspelled words on the right.")
        self.scheme_colors_hint = QLabel(hint.replace("%1", str(len(default_spellcheck_scheme()))), scheme_group)
        self.scheme_colors_hint.setWordWrap(True)
        scheme_layout.addWidget(self.scheme_colors_hint)

        self.scheme_colors_table = QTableWidget(0, 3, scheme_group)
        self.scheme_colors_table.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Text fill color"), self.tr("Underline color")])
        self.scheme_colors_table.verticalHeader().setVisible(False)
        self.scheme_colors_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.scheme_colors_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.scheme_colors_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.scheme_colors_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.scheme_colors_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.scheme_colors_table.cellDoubleClicked.connect(self._edit_scheme_color_cell)
        scheme_layout.addWidget(self.scheme_colors_table, 1)
        self._bind_checkbox_pair(self.show_main_window_after_capture, self.show_main_window_after_capture_checkbox)
        self._bind_checkbox_pair(self.hide_main_window_during_capture, self.hide_main_window_during_capture_checkbox)
        self._add_settings_page(
            "Application",
            "Application Settings",
            [
                application_group,
                application_details_group,
                capture_group,
            ],
        )
        self._add_settings_page(
            "Saver",
            "Saver Settings",
            [saver_group, saver_quality_group, saver_location_group],
            parent_title="Application",
        )
        self._add_settings_page("Tray Icon", "Tray Icon Settings", [tray_group, tray_defaults_group], parent_title="Application")
        self._add_settings_page(
            "Image Grabber",
            "Image Grabber Settings",
            [
                image_grabber_group,
                image_grabber_delay_group,
            ],
        )
        self._add_settings_page(
            "Snipping Area",
            "Snipping Area Settings",
            [
                snipping_area_group,
                snipping_area_appearance_group,
            ],
            parent_title="Image Grabber",
        )
        self._add_settings_page("Uploader", "Uploader Settings", [uploader_group])
        self._add_settings_page(
            "Imgur Uploader",
            "Imgur Uploader Settings",
            [
                self._create_placeholder_group(
                    self.tr("Imgur Uploader"),
                    [
                        self.tr("Native Imgur uploader parity is still pending."),
                    ],
                ),
            ],
            parent_title="Uploader",
        )
        self._add_settings_page(
            "FTP Uploader",
            "FTP Uploader Settings",
            [
                self._create_placeholder_group(
                    self.tr("FTP Uploader"),
                    [
                        self.tr("Native FTP uploader parity is still pending."),
                    ],
                ),
            ],
            parent_title="Uploader",
        )
        self._add_settings_page(
            "Script Uploader",
            "Script Uploader Settings",
            [upload_group],
            parent_title="Uploader",
        )
        self._add_settings_page("Annotator", "Annotator Settings", [annotator_group, annotator_appearance_group, editor_group])
        self._add_settings_page(
            "Stickers",
            "Sticker Settings",
            [
                self._create_placeholder_group(
                    self.tr("Stickers"),
                    [
                        self.tr("Sticker management and picker parity are still pending."),
                    ],
                ),
            ],
            parent_title="Annotator",
        )
        self._add_settings_page("Watermark", "Watermark Settings", [watermark_group], parent_title="Annotator")
        self._add_settings_page("HotKeys", "Global HotKeys", [shortcuts_group])
        self._add_settings_page(
            "Actions",
            "Action Settings",
            [
                self._build_actions_page(),
            ],
        )
        self._add_settings_page(
            "Plugins",
            "Plugin Settings",
            [
                self._build_plugins_page(),
            ],
        )
        self._add_settings_page("OCR", "OCR Settings", [ocr_group])
        self._add_settings_page(
            "Scheme colors",
            "Scheme colors",
            [scheme_group],
            parent_title="Annotator",
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_initial(initial)
        self._refresh_watermark_status()
        self.navigation_tree.expandAll()
        self.navigation_tree.setCurrentItem(self._navigation_order[0])

    def _create_placeholder_group(self, title: str, lines: list[str]) -> QGroupBox:
        group = QGroupBox(title, self)
        group_layout = QVBoxLayout(group)
        for line in lines:
            label = QLabel(line, group)
            label.setWordWrap(True)
            group_layout.addWidget(label)
        group_layout.addStretch(1)
        return group

    def _build_actions_page(self) -> QGroupBox:
        group = QGroupBox(self.tr("Actions"), self)
        layout = QVBoxLayout(group)

        add_button_row = QHBoxLayout()
        self.actions_add_button = QPushButton(self.tr("Add"), group)
        self.actions_add_button.setEnabled(False)
        add_button_row.addWidget(self.actions_add_button, 0)
        add_button_row.addStretch(1)
        layout.addLayout(add_button_row)

        self.actions_placeholder = QLabel(self.tr("Add new actions by pressing the 'Add' tab button."), group)
        self.actions_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.actions_placeholder.setStyleSheet("color: palette(mid);")
        self.actions_placeholder.setMinimumHeight(260)
        layout.addWidget(self.actions_placeholder, 1)
        return group

    def _build_plugins_page(self) -> QGroupBox:
        group = QGroupBox(self.tr("Plugins"), self)
        layout = QVBoxLayout(group)

        search_path_group = QGroupBox(self.tr("Search Path"), group)
        search_path_layout = QVBoxLayout(search_path_group)
        self.plugin_default_path = QRadioButton(self.tr("Default"), search_path_group)
        self.plugin_default_path.setChecked(True)
        self.plugin_default_path.setEnabled(False)
        self.plugin_custom_path = QRadioButton(search_path_group)
        self.plugin_custom_path.setEnabled(False)
        custom_path_row = QHBoxLayout()
        custom_path_row.addWidget(self.plugin_custom_path, 0)
        self.plugin_custom_path_edit = QLineEdit(search_path_group)
        self.plugin_custom_path_edit.setEnabled(False)
        custom_path_row.addWidget(self.plugin_custom_path_edit, 1)
        self.plugin_browse_button = QPushButton(self.tr("Browse"), search_path_group)
        self.plugin_browse_button.setEnabled(False)
        custom_path_row.addWidget(self.plugin_browse_button, 0)
        search_path_layout.addWidget(self.plugin_default_path)
        search_path_layout.addLayout(custom_path_row)
        layout.addWidget(search_path_group)

        plugins_row = QHBoxLayout()
        self.plugins_table = QTableWidget(6, 2, group)
        self.plugins_table.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Version")])
        self.plugins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.plugins_table.verticalHeader().setVisible(False)
        self.plugins_table.horizontalHeader().setStretchLastSection(True)
        for row in range(self.plugins_table.rowCount()):
            for column in range(self.plugins_table.columnCount()):
                self.plugins_table.setItem(row, column, QTableWidgetItem(""))
        plugins_row.addWidget(self.plugins_table, 1)

        detect_column = QVBoxLayout()
        self.plugin_detect_button = QPushButton(self.tr("Detect"), group)
        self.plugin_detect_button.setEnabled(False)
        detect_column.addWidget(self.plugin_detect_button)
        detect_column.addStretch(1)
        plugins_row.addLayout(detect_column)
        layout.addLayout(plugins_row, 1)

        return group

    @staticmethod
    def _scheme_color_display(color: QColor) -> str:
        return color.name(QColor.NameFormat.HexRgb)

    def _set_scheme_row(self, row: int, name: str, fill: QColor, underline: QColor) -> None:
        name_item = QTableWidgetItem(name)
        fill_item = QTableWidgetItem(self._scheme_color_display(fill))
        underline_item = QTableWidgetItem(self._scheme_color_display(underline))
        for item, color in ((fill_item, fill), (underline_item, underline)):
            item.setData(Qt.ItemDataRole.UserRole, QColor(color))
            item.setBackground(color)
            contrast = QColor("#ffffff" if color.lightness() < 128 else "#000000")
            item.setForeground(contrast)
        self.scheme_colors_table.setItem(row, 0, name_item)
        self.scheme_colors_table.setItem(row, 1, fill_item)
        self.scheme_colors_table.setItem(row, 2, underline_item)

    def _load_scheme_table(self, rows: list[tuple[str, QColor, QColor]]) -> None:
        self.scheme_colors_table.setRowCount(len(rows))
        for row_index, (name, fill, underline) in enumerate(rows):
            self._set_scheme_row(row_index, name, fill, underline)

    def _edit_scheme_color_cell(self, row: int, column: int) -> None:
        if column not in {1, 2}:
            return
        item = self.scheme_colors_table.item(row, column)
        if item is None:
            return
        current = item.data(Qt.ItemDataRole.UserRole)
        current_color = QColor(current) if isinstance(current, QColor) else QColor(item.text())
        color = QColorDialog.getColor(current_color, self, self.tr("Select color"))
        if not color.isValid():
            return
        name = self.scheme_colors_table.item(row, 0).text()
        fill_item = self.scheme_colors_table.item(row, 1)
        underline_item = self.scheme_colors_table.item(row, 2)
        fill_color = QColor(color if column == 1 else fill_item.data(Qt.ItemDataRole.UserRole))
        underline_color = QColor(color if column == 2 else underline_item.data(Qt.ItemDataRole.UserRole))
        self._set_scheme_row(row, name, fill_color, underline_color)

    def _wrap_page(self, title: str, groups: list[QWidget]) -> QWidget:
        host = QWidget(self)
        host_layout = QVBoxLayout(host)
        title_label = QLabel(title, host)
        title_font = title_label.font()
        title_font.setPointSize(title_font.pointSize() + 1)
        title_font.setBold(True)
        title_label.setFont(title_font)
        host_layout.addWidget(title_label)
        for group in groups:
            host_layout.addWidget(group)
        host_layout.addStretch(1)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(host)
        return scroll_area

    def _add_settings_page(
        self,
        navigation_title: str,
        page_title: str,
        groups: list[QWidget],
        *,
        parent_title: str | None = None,
    ) -> None:
        parent_item = self._navigation_items.get(parent_title) if parent_title else None
        item = QTreeWidgetItem(parent_item or self.navigation_tree, [self.tr(navigation_title)])
        page_index = self.page_stack.addWidget(self._wrap_page(self.tr(page_title), groups))
        item.setData(0, Qt.ItemDataRole.UserRole, page_index)
        item.setData(0, Qt.ItemDataRole.UserRole + 1, navigation_title.lower())
        self._navigation_items[navigation_title] = item
        self._navigation_order.append(item)

    def _show_settings_page(self, item: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None = None) -> None:
        if item is None:
            return
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if not isinstance(index, int):
            return
        if index < 0 or index >= self.page_stack.count():
            return
        self.page_stack.setCurrentIndex(index)

    def _filter_navigation_items(self, text: str) -> None:
        normalized = text.strip().lower()
        direct_matches = {
            id(item): not normalized
            or normalized in str(item.data(0, Qt.ItemDataRole.UserRole + 1) or item.text(0).lower())
            for item in self._navigation_order
        }

        def has_matching_descendant(item: QTreeWidgetItem) -> bool:
            return any(
                direct_matches.get(id(item.child(index)), False) or has_matching_descendant(item.child(index))
                for index in range(item.childCount())
            )

        def has_matching_ancestor(item: QTreeWidgetItem) -> bool:
            parent = item.parent()
            while parent is not None:
                if direct_matches.get(id(parent), False):
                    return True
                parent = parent.parent()
            return False

        first_visible_item = None
        for item in self._navigation_order:
            visible = direct_matches[id(item)] or has_matching_descendant(item) or has_matching_ancestor(item)
            item.setHidden(not visible)
            if visible and direct_matches[id(item)] and first_visible_item is None:
                first_visible_item = item
        if first_visible_item is not None and self.navigation_tree.currentItem() is not first_visible_item:
            self.navigation_tree.setCurrentItem(first_visible_item)

    def _bind_checkbox_pair(self, first: QCheckBox, second: QCheckBox) -> None:
        def sync(source: QCheckBox, target: QCheckBox) -> None:
            target.blockSignals(True)
            target.setChecked(source.isChecked())
            target.blockSignals(False)

        first.toggled.connect(lambda _checked: sync(first, second))
        second.toggled.connect(lambda _checked: sync(second, first))

    def _apply_initial(self, initial: SettingsData) -> None:
        tool_index = self.tool_combo.findData(initial.tool)
        if tool_index >= 0:
            self.tool_combo.setCurrentIndex(tool_index)
        self.pen_width.setValue(initial.pen_width)
        self.font_family.setCurrentFont(QFont(initial.font_family))
        self.font_size.setValue(initial.font_point_size)
        fill_mode_index = self.fill_mode.findData(initial.fill_mode)
        if fill_mode_index >= 0:
            self.fill_mode.setCurrentIndex(fill_mode_index)
        self.opacity.setValue(initial.opacity_percent)
        self.bold.setChecked(initial.bold)
        self.italic.setChecked(initial.italic)
        self.rotate_watermark.setChecked(initial.rotate_watermark)
        self.capture_delay_seconds.setValue(initial.capture_delay_seconds)
        self.implicit_capture_delay.setValue(initial.capture_implicit_delay_ms)
        self.capture_mouse_cursor.setChecked(initial.capture_include_cursor)
        self.force_generic_wayland.setChecked(initial.force_generic_wayland)
        self.scale_generic_wayland.setChecked(initial.scale_generic_wayland)
        self.hide_main_window_during_capture.setChecked(initial.hide_main_window_during_capture)
        self.show_main_window_after_capture.setChecked(initial.show_main_window_after_capture)
        self.auto_copy_new_captures.setChecked(initial.auto_copy_new_captures)
        self.remember_window_position.setChecked(initial.application_remember_position)
        self.auto_hide_tabs.setChecked(initial.application_auto_hide_tabs)
        self.capture_on_startup.setChecked(initial.application_capture_on_startup)
        self.auto_hide_docks.setChecked(initial.application_auto_hide_docks)
        self.auto_resize_to_content.setChecked(initial.application_auto_resize_to_content)
        self.run_single_instance.setChecked(initial.application_single_instance)
        self.resize_delay.setValue(initial.application_resize_delay_ms)
        language_index = self.application_language.findData(initial.application_language)
        if language_index >= 0:
            self.application_language.setCurrentIndex(language_index)
        self.saver_prompt_discard.setChecked(initial.saver_prompt_discard)
        self.saver_remember_directory.setChecked(initial.saver_remember_directory)
        self.saver_quality_factor.setChecked(initial.saver_quality_enabled)
        self.saver_quality_default.setChecked(not initial.saver_quality_enabled)
        self.saver_quality_value.setValue(initial.saver_quality_factor)
        self.saver_quality_value.setEnabled(initial.saver_quality_enabled)
        self.saver_auto_save.setChecked(initial.saver_auto_save)
        self.saver_location.setText(initial.saver_location)
        self.saver_overwrite.setChecked(initial.saver_overwrite)
        self.use_tray_icon.setChecked(initial.use_tray_icon)
        self.minimize_to_tray.setChecked(initial.minimize_to_tray)
        self.close_to_tray.setChecked(initial.close_to_tray)
        self.start_minimized_to_tray.setChecked(initial.start_minimized_to_tray)
        self.tray_notifications.setChecked(initial.tray_notifications)
        tray_default_action_index = self.tray_default_action.findData(initial.tray_default_action)
        if tray_default_action_index >= 0:
            self.tray_default_action.setCurrentIndex(tray_default_action_index)
        tray_default_capture_mode_index = self.tray_default_capture_mode.findData(initial.tray_default_capture_mode)
        if tray_default_capture_mode_index >= 0:
            self.tray_default_capture_mode.setCurrentIndex(tray_default_capture_mode_index)
        self._sync_tray_controls(initial.use_tray_icon)
        self.enable_global_hotkeys.setChecked(initial.shortcuts_enabled)
        for key, value in initial.shortcuts.items():
            if key in self.shortcut_edits:
                self.shortcut_edits[key].setKeySequence(QKeySequence(value))
        self._sync_shortcut_controls(initial.shortcuts_enabled)
        self.ask_confirmation_before_uploading.setChecked(initial.upload_confirm_before_uploading)
        self.upload_script_path.setText(initial.upload_script_path)
        self.upload_copy_output.setChecked(initial.upload_copy_output)
        self.upload_output_filter.setText(initial.upload_output_filter)
        self.upload_stop_on_stderr.setChecked(initial.upload_stop_on_stderr)
        self.ocr_enabled.setChecked(initial.ocr_enabled)
        backend_index = self.ocr_backend.findData(initial.ocr_backend)
        if backend_index >= 0:
            self.ocr_backend.setCurrentIndex(backend_index)
        language_index = self.ocr_language.findData(initial.ocr_language)
        if language_index >= 0:
            self.ocr_language.setCurrentIndex(language_index)
        self.ocr_copy_to_clipboard.setChecked(initial.ocr_copy_to_clipboard)
        self.ocr_script_path.setText(initial.ocr_script_path)
        scheme_rows = [
            (name, QColor(fill), QColor(underline))
            for name, fill, underline in (initial.spellcheck_scheme or [])
        ] or load_spellcheck_scheme()
        self._load_scheme_table(scheme_rows)
        self._sync_ocr_controls()

    def _refresh_watermark_status(self) -> None:
        pixmap = self._watermark_store.load()
        if pixmap.isNull():
            self.watermark_status.setText(self.tr("No watermark image configured"))
            return
        status = self.tr("%1x%2 image configured")
        self.watermark_status.setText(status.replace("%1", str(pixmap.width())).replace("%2", str(pixmap.height())))

    def _update_watermark_image(self) -> None:
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select watermark image"),
            "",
            self.tr("Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"),
        )
        if not path:
            return
        if not self._watermark_store.save_from_path(path):
            message = self.tr("Unable to load watermark image: %1").replace("%1", path)
            QMessageBox.critical(self, self.tr("Settings"), message)
            return
        self._refresh_watermark_status()

    def _sync_tray_controls(self, enabled: bool) -> None:
        self.minimize_to_tray.setEnabled(enabled)
        self.close_to_tray.setEnabled(enabled)
        self.start_minimized_to_tray.setEnabled(enabled)
        self.tray_notifications.setEnabled(enabled)
        self.tray_default_action.setEnabled(enabled)
        self._sync_tray_default_controls()

    def _sync_tray_default_controls(self) -> None:
        tray_enabled = self.use_tray_icon.isChecked()
        capture_enabled = tray_enabled and self.tray_default_action.currentData() == "capture"
        self.tray_default_capture_mode.setEnabled(capture_enabled)

    def _sync_shortcut_controls(self, enabled: bool) -> None:
        for editor in self.shortcut_edits.values():
            editor.setEnabled(enabled)
        for button in self.shortcut_clear_buttons:
            button.setEnabled(enabled)

    def _select_upload_script(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, self.tr("Select upload script"), self.upload_script_path.text() or "")
        if path:
            self.upload_script_path.setText(path)

    def _select_saver_location(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        current = self.saver_location.text().strip() or str(Path.home() / "Pictures" / "$Y$M$D-$T.png")
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Capture save location and filename"),
            current,
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;WebP (*.webp)",
        )
        if path:
            self.saver_location.setText(path)

    def _select_ocr_script(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, self.tr("Select OCR script"), self.ocr_script_path.text() or "")
        if path:
            self.ocr_script_path.setText(path)

    def _sync_ocr_controls(self) -> None:
        enabled = self.ocr_enabled.isChecked()
        backend = self.ocr_backend.currentData()
        self.ocr_backend.setEnabled(enabled)
        self.ocr_language.setEnabled(enabled and backend == "paddleocr")
        self.ocr_copy_to_clipboard.setEnabled(enabled)
        self.ocr_script_path.setEnabled(enabled and backend == "script")
        self.ocr_script_button.setEnabled(enabled and backend == "script")

    def settings_data(self) -> SettingsData:
        spellcheck_scheme: list[tuple[str, str, str]] = []
        for row in range(self.scheme_colors_table.rowCount()):
            name_item = self.scheme_colors_table.item(row, 0)
            fill_item = self.scheme_colors_table.item(row, 1)
            underline_item = self.scheme_colors_table.item(row, 2)
            if name_item is None or fill_item is None or underline_item is None:
                continue
            fill_color = fill_item.data(Qt.ItemDataRole.UserRole)
            underline_color = underline_item.data(Qt.ItemDataRole.UserRole)
            spellcheck_scheme.append(
                (
                    name_item.text(),
                    QColor(fill_color).name(QColor.NameFormat.HexRgb),
                    QColor(underline_color).name(QColor.NameFormat.HexRgb),
                )
            )
        return SettingsData(
            tool=self.tool_combo.currentData(),
            pen_width=self.pen_width.value(),
            font_family=self.font_family.currentFont().family(),
            font_point_size=self.font_size.value(),
            fill_mode=self.fill_mode.currentData(),
            opacity_percent=self.opacity.value(),
            bold=self.bold.isChecked(),
            italic=self.italic.isChecked(),
            rotate_watermark=self.rotate_watermark.isChecked(),
            capture_delay_seconds=self.capture_delay_seconds.value(),
            capture_implicit_delay_ms=self.implicit_capture_delay.value(),
            capture_include_cursor=self.capture_mouse_cursor.isChecked(),
            force_generic_wayland=self.force_generic_wayland.isChecked(),
            scale_generic_wayland=self.scale_generic_wayland.isChecked(),
            hide_main_window_during_capture=self.hide_main_window_during_capture.isChecked(),
            show_main_window_after_capture=self.show_main_window_after_capture.isChecked(),
            auto_copy_new_captures=self.auto_copy_new_captures.isChecked(),
            application_remember_position=self.remember_window_position.isChecked(),
            application_auto_hide_tabs=self.auto_hide_tabs.isChecked(),
            application_capture_on_startup=self.capture_on_startup.isChecked(),
            application_auto_hide_docks=self.auto_hide_docks.isChecked(),
            application_auto_resize_to_content=self.auto_resize_to_content.isChecked(),
            application_single_instance=self.run_single_instance.isChecked(),
            application_resize_delay_ms=self.resize_delay.value(),
            application_language=str(self.application_language.currentData()),
            saver_prompt_discard=self.saver_prompt_discard.isChecked(),
            saver_remember_directory=self.saver_remember_directory.isChecked(),
            saver_quality_enabled=self.saver_quality_factor.isChecked(),
            saver_quality_factor=self.saver_quality_value.value(),
            saver_auto_save=self.saver_auto_save.isChecked(),
            saver_location=self.saver_location.text().strip(),
            saver_overwrite=self.saver_overwrite.isChecked(),
            use_tray_icon=self.use_tray_icon.isChecked(),
            minimize_to_tray=self.minimize_to_tray.isChecked(),
            close_to_tray=self.close_to_tray.isChecked(),
            start_minimized_to_tray=self.start_minimized_to_tray.isChecked(),
            tray_notifications=self.tray_notifications.isChecked(),
            tray_default_action=str(self.tray_default_action.currentData()),
            tray_default_capture_mode=str(self.tray_default_capture_mode.currentData()),
            shortcuts_enabled=self.enable_global_hotkeys.isChecked(),
            shortcuts={
                key: editor.keySequence().toString(QKeySequence.SequenceFormat.NativeText)
                for key, editor in self.shortcut_edits.items()
            },
            upload_confirm_before_uploading=self.ask_confirmation_before_uploading.isChecked(),
            upload_script_path=self.upload_script_path.text().strip(),
            upload_copy_output=self.upload_copy_output.isChecked(),
            upload_output_filter=self.upload_output_filter.text(),
            upload_stop_on_stderr=self.upload_stop_on_stderr.isChecked(),
            ocr_enabled=self.ocr_enabled.isChecked(),
            ocr_backend=str(self.ocr_backend.currentData()),
            ocr_language=str(self.ocr_language.currentData()),
            ocr_copy_to_clipboard=self.ocr_copy_to_clipboard.isChecked(),
            ocr_script_path=self.ocr_script_path.text().strip(),
            spellcheck_scheme=spellcheck_scheme,
        )
