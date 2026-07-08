from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QFont, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .canvas import FillMode, Tool
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
    hide_main_window_during_capture: bool
    show_main_window_after_capture: bool
    auto_copy_new_captures: bool
    use_tray_icon: bool
    minimize_to_tray: bool
    close_to_tray: bool
    start_minimized_to_tray: bool
    tray_notifications: bool
    shortcuts: dict[str, str]
    upload_script_path: str
    upload_copy_output: bool
    upload_output_filter: str
    upload_stop_on_stderr: bool
    ocr_enabled: bool
    ocr_backend: str
    ocr_language: str
    ocr_copy_to_clipboard: bool
    ocr_script_path: str


class SettingsDialog(QDialog):
    def __init__(self, initial: SettingsData, watermark_store: WatermarkStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._watermark_store = watermark_store
        self.setWindowTitle("Settings")
        self.resize(900, 700)

        layout = QVBoxLayout(self)
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout, 1)

        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Search Settings...")
        self.navigation_list = QListWidget(self)
        self.navigation_list.setMaximumWidth(220)
        self.navigation_list.currentRowChanged.connect(self._show_settings_page)
        self.search_line_edit.textChanged.connect(self._filter_navigation_items)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.search_line_edit)
        left_layout.addWidget(self.navigation_list, 1)

        left_host = QWidget(self)
        left_host.setLayout(left_layout)
        content_layout.addWidget(left_host)

        self.page_stack = QStackedWidget(self)
        content_layout.addWidget(self.page_stack, 1)

        editor_group = QGroupBox("Editor Defaults", self)
        editor_layout = QFormLayout(editor_group)

        self.tool_combo = QComboBox(editor_group)
        self.tool_combo.addItem("Select", Tool.SELECT)
        self.tool_combo.addItem("Pen", Tool.PEN)
        self.tool_combo.addItem("Line", Tool.LINE)
        self.tool_combo.addItem("Arrow", Tool.ARROW)
        self.tool_combo.addItem("Rectangle", Tool.RECT)
        self.tool_combo.addItem("Ellipse", Tool.ELLIPSE)
        self.tool_combo.addItem("Text", Tool.TEXT)
        self.tool_combo.addItem("Blur", Tool.BLUR)
        self.tool_combo.addItem("Pixelate", Tool.PIXELATE)
        self.tool_combo.addItem("Crop", Tool.CROP)
        editor_layout.addRow("Default Tool", self.tool_combo)

        self.pen_width = QSpinBox(editor_group)
        self.pen_width.setRange(1, 20)
        editor_layout.addRow("Stroke Width", self.pen_width)

        self.font_family = QFontComboBox(editor_group)
        editor_layout.addRow("Font Family", self.font_family)

        self.font_size = QSpinBox(editor_group)
        self.font_size.setRange(6, 144)
        editor_layout.addRow("Font Size", self.font_size)

        self.fill_mode = QComboBox(editor_group)
        self.fill_mode.addItem("Stroke", FillMode.STROKE_ONLY)
        self.fill_mode.addItem("Fill", FillMode.FILL_ONLY)
        self.fill_mode.addItem("Stroke+Fill", FillMode.STROKE_AND_FILL)
        editor_layout.addRow("Shape Fill Mode", self.fill_mode)

        self.opacity = QSpinBox(editor_group)
        self.opacity.setRange(0, 100)
        editor_layout.addRow("Opacity %", self.opacity)

        style_row = QHBoxLayout()
        self.bold = QCheckBox("Bold", editor_group)
        self.italic = QCheckBox("Italic", editor_group)
        style_row.addWidget(self.bold)
        style_row.addWidget(self.italic)
        style_host = QWidget(editor_group)
        style_host.setLayout(style_row)
        editor_layout.addRow("Text Style", style_host)

        watermark_group = QGroupBox("Watermark", self)
        watermark_layout = QFormLayout(watermark_group)

        self.rotate_watermark = QCheckBox("Rotate Watermark 45°", watermark_group)
        watermark_layout.addRow(self.rotate_watermark)

        image_row = QHBoxLayout()
        self.watermark_status = QLabel(watermark_group)
        self.update_watermark_button = QPushButton("Update Image…", watermark_group)
        self.update_watermark_button.clicked.connect(self._update_watermark_image)
        image_row.addWidget(self.watermark_status, 1)
        image_row.addWidget(self.update_watermark_button)
        image_host = QWidget(watermark_group)
        image_host.setLayout(image_row)
        watermark_layout.addRow("Stored Image", image_host)

        application_group = QGroupBox("Application", self)
        application_layout = QVBoxLayout(application_group)

        self.auto_copy_new_captures = QCheckBox("Automatically copy new captures to clipboard", application_group)
        application_layout.addWidget(self.auto_copy_new_captures)

        self.remember_window_position = QCheckBox("Remember Main Window position on move and load on startup", application_group)
        self.remember_window_position.setChecked(True)
        self.remember_window_position.setEnabled(False)
        application_layout.addWidget(self.remember_window_position)

        self.capture_on_startup = QCheckBox("Capture screenshot at startup with default mode", application_group)
        self.capture_on_startup.setEnabled(False)
        application_layout.addWidget(self.capture_on_startup)

        self.use_tabs = QCheckBox("Use Tabs", application_group)
        self.use_tabs.setChecked(True)
        self.use_tabs.setEnabled(False)
        application_layout.addWidget(self.use_tabs)

        self.auto_hide_tabs = QCheckBox("Auto hide Tabs", application_group)
        self.auto_hide_tabs.setEnabled(False)
        application_layout.addWidget(self.auto_hide_tabs)

        self.run_single_instance = QCheckBox("Run ksnip as single instance", application_group)
        self.run_single_instance.setEnabled(False)
        application_layout.addWidget(self.run_single_instance)

        self.auto_hide_docks = QCheckBox("Auto hide Docks", application_group)
        self.auto_hide_docks.setEnabled(False)
        application_layout.addWidget(self.auto_hide_docks)

        self.auto_resize_to_content = QCheckBox("Auto resize to content", application_group)
        self.auto_resize_to_content.setEnabled(False)
        application_layout.addWidget(self.auto_resize_to_content)

        self.enable_debugging = QCheckBox("Enable Debugging", application_group)
        self.enable_debugging.setEnabled(False)
        application_layout.addWidget(self.enable_debugging)

        application_details_group = QGroupBox("Appearance and Paths", self)
        application_details_layout = QFormLayout(application_details_group)

        self.resize_delay = QSpinBox(application_details_group)
        self.resize_delay.setRange(0, 1000)
        self.resize_delay.setSuffix(" ms")
        self.resize_delay.setValue(10)
        self.resize_delay.setEnabled(False)
        application_details_layout.addRow("Resize delay", self.resize_delay)

        self.application_style = QComboBox(application_details_group)
        self.application_style.addItems(["Fusion", "Windows"])
        self.application_style.setEnabled(False)
        application_details_layout.addRow("Application Style", self.application_style)

        temp_directory_row = QHBoxLayout()
        self.temp_directory = QLineEdit("/tmp", application_details_group)
        self.temp_directory.setEnabled(False)
        self.temp_directory_browse = QPushButton("Browse", application_details_group)
        self.temp_directory_browse.setEnabled(False)
        temp_directory_row.addWidget(self.temp_directory, 1)
        temp_directory_row.addWidget(self.temp_directory_browse)
        temp_directory_host = QWidget(application_details_group)
        temp_directory_host.setLayout(temp_directory_row)
        application_details_layout.addRow("Temp Directory", temp_directory_host)

        capture_group = QGroupBox("Capture", self)
        capture_layout = QFormLayout(capture_group)

        self.capture_delay_seconds = QSpinBox(capture_group)
        self.capture_delay_seconds.setRange(0, 60)
        self.capture_delay_seconds.setSuffix(" s")
        capture_layout.addRow("Capture Delay", self.capture_delay_seconds)

        self.hide_main_window_during_capture = QCheckBox("Hide Main Window During Capture", capture_group)
        self.show_main_window_after_capture = QCheckBox("Show Main Window After Capture", capture_group)
        capture_layout.addRow(self.hide_main_window_during_capture)
        capture_layout.addRow(self.show_main_window_after_capture)
        tray_group = QGroupBox("Tray Icon", self)
        tray_layout = QFormLayout(tray_group)

        self.use_tray_icon = QCheckBox("Use Tray Icon", tray_group)
        self.minimize_to_tray = QCheckBox("Minimize To Tray", tray_group)
        self.close_to_tray = QCheckBox("Close To Tray", tray_group)
        self.start_minimized_to_tray = QCheckBox("Start Minimized To Tray", tray_group)
        self.tray_notifications = QCheckBox("Display Tray Notifications", tray_group)
        tray_layout.addRow(self.use_tray_icon)
        tray_layout.addRow(self.minimize_to_tray)
        tray_layout.addRow(self.close_to_tray)
        tray_layout.addRow(self.start_minimized_to_tray)
        tray_layout.addRow(self.tray_notifications)
        self.use_tray_icon.toggled.connect(self._sync_tray_controls)

        tray_defaults_group = QGroupBox("Default Action", self)
        tray_defaults_layout = QFormLayout(tray_defaults_group)
        self.tray_default_action = QComboBox(tray_defaults_group)
        self.tray_default_action.addItems(["Show Editor", "Capture"])
        self.tray_default_action.setEnabled(False)
        tray_defaults_layout.addRow("Action", self.tray_default_action)

        self.tray_default_capture_mode = QComboBox(tray_defaults_group)
        self.tray_default_capture_mode.addItems(["Rect Area", "Last Rect Area", "Full Screen", "Current Screen", "Active Window", "Window Under Cursor"])
        self.tray_default_capture_mode.setEnabled(False)
        tray_defaults_layout.addRow("Capture Mode", self.tray_default_capture_mode)
        shortcuts_group = QGroupBox("Hotkeys", self)
        shortcuts_layout = QFormLayout(shortcuts_group)
        self.shortcut_edits: dict[str, QKeySequenceEdit] = {}
        for key, label in (
            ("capture_rect", "Rect Area Capture"),
            ("capture_last_rect", "Last Rect Area Capture"),
            ("capture_full", "Full Screen Capture"),
            ("capture_current", "Current Screen Capture"),
            ("capture_active", "Active Window Capture"),
            ("capture_under_cursor", "Window Under Cursor Capture"),
            ("open", "Open Image"),
            ("save", "Save"),
            ("paste", "Paste Image"),
            ("pin", "Pin Image"),
            ("watermark", "Add Watermark"),
            ("upload", "Upload Image"),
            ("ocr", "OCR Text Recognition"),
        ):
            editor = QKeySequenceEdit(shortcuts_group)
            self.shortcut_edits[key] = editor
            shortcuts_layout.addRow(label, editor)
        upload_group = QGroupBox("Uploader", self)
        upload_layout = QFormLayout(upload_group)
        script_row = QHBoxLayout()
        self.upload_script_path = QLineEdit(upload_group)
        self.upload_script_button = QPushButton("Browse…", upload_group)
        self.upload_script_button.clicked.connect(self._select_upload_script)
        script_row.addWidget(self.upload_script_path, 1)
        script_row.addWidget(self.upload_script_button)
        script_host = QWidget(upload_group)
        script_host.setLayout(script_row)
        upload_layout.addRow("Script Path", script_host)

        self.upload_copy_output = QCheckBox("Copy script output to clipboard", upload_group)
        upload_layout.addRow(self.upload_copy_output)

        self.upload_output_filter = QLineEdit(upload_group)
        upload_layout.addRow("Output Filter Regex", self.upload_output_filter)

        self.upload_stop_on_stderr = QCheckBox("Treat stderr as failure", upload_group)
        upload_layout.addRow(self.upload_stop_on_stderr)
        ocr_group = QGroupBox("OCR", self)
        ocr_layout = QFormLayout(ocr_group)
        self.ocr_enabled = QCheckBox("Enable OCR actions", ocr_group)
        self.ocr_backend = QComboBox(ocr_group)
        self.ocr_backend.addItem("PaddleOCR", "paddleocr")
        self.ocr_backend.addItem("Script", "script")
        self.ocr_language = QComboBox(ocr_group)
        self.ocr_language.addItem("English", "english")
        self.ocr_language.addItem("Spanish", "spanish")
        self.ocr_language.addItem("Spanish + English (script backend recommended)", "spanish_english")
        self.ocr_copy_to_clipboard = QCheckBox("Copy OCR result to clipboard automatically", ocr_group)
        ocr_script_row = QHBoxLayout()
        self.ocr_script_path = QLineEdit(ocr_group)
        self.ocr_script_button = QPushButton("Browse…", ocr_group)
        self.ocr_script_button.clicked.connect(self._select_ocr_script)
        ocr_script_row.addWidget(self.ocr_script_path, 1)
        ocr_script_row.addWidget(self.ocr_script_button)
        ocr_script_host = QWidget(ocr_group)
        ocr_script_host.setLayout(ocr_script_row)
        ocr_layout.addRow(self.ocr_enabled)
        ocr_layout.addRow("Backend", self.ocr_backend)
        ocr_layout.addRow("Language", self.ocr_language)
        ocr_layout.addRow(self.ocr_copy_to_clipboard)
        ocr_layout.addRow("Script Path", ocr_script_host)
        self.ocr_enabled.toggled.connect(self._sync_ocr_controls)
        self.ocr_backend.currentIndexChanged.connect(self._sync_ocr_controls)
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
            [
                self._create_placeholder_group(
                    "Saver",
                    [
                        "Save path templates, quality controls, and advanced saver options are still pending parity.",
                    ],
                ),
            ],
        )
        self._add_settings_page("Tray Icon", "Tray Icon Settings", [tray_group, tray_defaults_group])
        self._add_settings_page(
            "Image Grabber",
            "Image Grabber Settings",
            [
                self._create_placeholder_group(
                    "Image Grabber",
                    [
                        "Portal, cursor, Wayland/X11 options, and implicit capture delay are not yet fully ported.",
                    ],
                ),
            ],
        )
        self._add_settings_page(
            "Snipping Area",
            "Snipping Area Settings",
            [
                self._create_placeholder_group(
                    "Snipping Area",
                    [
                        "Fine-grained snipping overlay settings are still pending parity with the C++ dialog.",
                    ],
                ),
            ],
        )
        self._add_settings_page("Uploader", "Uploader Settings", [upload_group, ocr_group])
        self._add_settings_page(
            "Imgur Uploader",
            "Imgur Uploader Settings",
            [
                self._create_placeholder_group(
                    "Imgur Uploader",
                    [
                        "Native Imgur uploader parity is still pending.",
                    ],
                ),
            ],
        )
        self._add_settings_page(
            "FTP Uploader",
            "FTP Uploader Settings",
            [
                self._create_placeholder_group(
                    "FTP Uploader",
                    [
                        "Native FTP uploader parity is still pending.",
                    ],
                ),
            ],
        )
        self._add_settings_page(
            "Script Uploader",
            "Script Uploader Settings",
            [
                self._create_placeholder_group(
                    "Script Uploader",
                    [
                        "This subpage is reserved for a more faithful port of the dedicated Script Uploader view.",
                        "Current script uploader options are available on the main Uploader page.",
                    ],
                ),
            ],
        )
        self._add_settings_page("Annotator", "Annotator Settings", [editor_group])
        self._add_settings_page(
            "Stickers",
            "Sticker Settings",
            [
                self._create_placeholder_group(
                    "Stickers",
                    [
                        "Sticker management and picker parity are still pending.",
                    ],
                ),
            ],
        )
        self._add_settings_page("Watermark", "Watermark Settings", [watermark_group])
        self._add_settings_page("HotKeys", "HotKey Settings", [shortcuts_group])
        self._add_settings_page(
            "Actions",
            "Action Settings",
            [
                self._create_placeholder_group(
                    "Actions",
                    [
                        "Post-capture action pipelines and per-action configuration are still pending.",
                    ],
                ),
            ],
        )
        self._add_settings_page(
            "Plugins",
            "Plugin Settings",
            [
                self._create_placeholder_group(
                    "Plugins",
                    [
                        "Plugin system parity is still pending for the PyQt6 port.",
                    ],
                ),
            ],
        )

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_initial(initial)
        self._refresh_watermark_status()
        self.navigation_list.setCurrentRow(0)

    def _create_placeholder_group(self, title: str, lines: list[str]) -> QGroupBox:
        group = QGroupBox(title, self)
        group_layout = QVBoxLayout(group)
        for line in lines:
            label = QLabel(line, group)
            label.setWordWrap(True)
            group_layout.addWidget(label)
        group_layout.addStretch(1)
        return group

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

    def _add_settings_page(self, navigation_title: str, page_title: str, groups: list[QWidget]) -> None:
        item = QListWidgetItem(navigation_title, self.navigation_list)
        item.setData(256, navigation_title.lower())
        self.page_stack.addWidget(self._wrap_page(page_title, groups))

    def _show_settings_page(self, index: int) -> None:
        if index < 0 or index >= self.page_stack.count():
            return
        self.page_stack.setCurrentIndex(index)

    def _filter_navigation_items(self, text: str) -> None:
        normalized = text.strip().lower()
        first_visible_row = -1
        for row in range(self.navigation_list.count()):
            item = self.navigation_list.item(row)
            haystack = str(item.data(256) or item.text().lower())
            hidden = bool(normalized) and normalized not in haystack
            item.setHidden(hidden)
            if not hidden and first_visible_row < 0:
                first_visible_row = row
        if first_visible_row >= 0 and self.navigation_list.currentRow() != first_visible_row:
            self.navigation_list.setCurrentRow(first_visible_row)

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
        self.hide_main_window_during_capture.setChecked(initial.hide_main_window_during_capture)
        self.show_main_window_after_capture.setChecked(initial.show_main_window_after_capture)
        self.auto_copy_new_captures.setChecked(initial.auto_copy_new_captures)
        self.use_tray_icon.setChecked(initial.use_tray_icon)
        self.minimize_to_tray.setChecked(initial.minimize_to_tray)
        self.close_to_tray.setChecked(initial.close_to_tray)
        self.start_minimized_to_tray.setChecked(initial.start_minimized_to_tray)
        self.tray_notifications.setChecked(initial.tray_notifications)
        self._sync_tray_controls(initial.use_tray_icon)
        for key, value in initial.shortcuts.items():
            if key in self.shortcut_edits:
                self.shortcut_edits[key].setKeySequence(QKeySequence(value))
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
        self._sync_ocr_controls()

    def _refresh_watermark_status(self) -> None:
        pixmap = self._watermark_store.load()
        if pixmap.isNull():
            self.watermark_status.setText("No watermark image configured")
            return
        self.watermark_status.setText(f"{pixmap.width()}x{pixmap.height()} image configured")

    def _update_watermark_image(self) -> None:
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select watermark image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
        )
        if not path:
            return
        if not self._watermark_store.save_from_path(path):
            QMessageBox.critical(self, "Settings", f"Unable to load watermark image: {path}")
            return
        self._refresh_watermark_status()

    def _sync_tray_controls(self, enabled: bool) -> None:
        self.minimize_to_tray.setEnabled(enabled)
        self.close_to_tray.setEnabled(enabled)
        self.start_minimized_to_tray.setEnabled(enabled)
        self.tray_notifications.setEnabled(enabled)

    def _select_upload_script(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Select upload script", self.upload_script_path.text() or "")
        if path:
            self.upload_script_path.setText(path)

    def _select_ocr_script(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(self, "Select OCR script", self.ocr_script_path.text() or "")
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
            hide_main_window_during_capture=self.hide_main_window_during_capture.isChecked(),
            show_main_window_after_capture=self.show_main_window_after_capture.isChecked(),
            auto_copy_new_captures=self.auto_copy_new_captures.isChecked(),
            use_tray_icon=self.use_tray_icon.isChecked(),
            minimize_to_tray=self.minimize_to_tray.isChecked(),
            close_to_tray=self.close_to_tray.isChecked(),
            start_minimized_to_tray=self.start_minimized_to_tray.isChecked(),
            tray_notifications=self.tray_notifications.isChecked(),
            shortcuts={
                key: editor.keySequence().toString(QKeySequence.SequenceFormat.NativeText)
                for key, editor in self.shortcut_edits.items()
            },
            upload_script_path=self.upload_script_path.text().strip(),
            upload_copy_output=self.upload_copy_output.isChecked(),
            upload_output_filter=self.upload_output_filter.text(),
            upload_stop_on_stderr=self.upload_stop_on_stderr.isChecked(),
            ocr_enabled=self.ocr_enabled.isChecked(),
            ocr_backend=str(self.ocr_backend.currentData()),
            ocr_language=str(self.ocr_language.currentData()),
            ocr_copy_to_clipboard=self.ocr_copy_to_clipboard.isChecked(),
            ocr_script_path=self.ocr_script_path.text().strip(),
        )
