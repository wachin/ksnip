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
    QPushButton,
    QSpinBox,
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
        self.resize(720, 780)

        layout = QVBoxLayout(self)

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

        layout.addWidget(editor_group)

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

        layout.addWidget(watermark_group)

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
        layout.addWidget(tray_group)

        shortcuts_group = QGroupBox("Hotkeys", self)
        shortcuts_layout = QFormLayout(shortcuts_group)
        self.shortcut_edits: dict[str, QKeySequenceEdit] = {}
        for key, label in (
            ("capture_rect", "Rect Area Capture"),
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
        layout.addWidget(shortcuts_group)

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
        layout.addWidget(upload_group)

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
        layout.addWidget(ocr_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._apply_initial(initial)
        self._refresh_watermark_status()

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
